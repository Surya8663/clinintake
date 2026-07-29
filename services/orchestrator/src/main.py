from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel
from contextlib import asynccontextmanager

from services.common.jwt_verifier import get_current_user_claims, require_roles, require_m2m_service
from services.common.security_headers import SecurityHeadersMiddleware
from src.config import settings
from src.logger import logger
from src.state_machine import DocumentWorkflow, transition_workflow
from src.persistence import persistence
from src.dispatcher import audit_event_bus, dispatch_downstream_call
from src.contracts import (
    SanitizeRequest, SanitizeResponse,
    ExtractRequest, ExtractResponse,
    ValidateRequest, ValidateResponse,
    ReasonRequest, ReasonResponse,
    EHRWriteRequest, EHRWriteResponse
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting up {settings.service_name}")
    await audit_event_bus.start()
    yield
    logger.info(f"Shutting down {settings.service_name}")
    await audit_event_bus.stop()
    await persistence.close()

app = FastAPI(
    title=settings.service_name,
    description="Workflow Orchestrator central hub",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(SecurityHeadersMiddleware)

class CreateDocumentRequest(BaseModel):
    document_id: str
    file_path: str

class TransitionRequest(BaseModel):
    trigger: str
    context: Optional[Dict[str, Any]] = None

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception in Orchestrator", extra={"error": str(exc), "path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.service_name}

@app.post("/orchestrator/documents")
async def create_document(
    req: CreateDocumentRequest,
    claims: Dict[str, Any] = Depends(get_current_user_claims)
):
    existing = await persistence.get_workflow(req.document_id)
    if existing:
        raise HTTPException(status_code=400, detail="Document already exists")
    
    workflow = DocumentWorkflow(
        document_id=req.document_id,
        state="received",
        context={"file_path": req.file_path}
    )
    await persistence.save_workflow(workflow)
    
    await audit_event_bus.publish_event(
        event_type="document_received",
        document_id=req.document_id,
        payload={"file_path": req.file_path}
    )
    
    return {"document_id": workflow.document_id, "state": workflow.state, "context": workflow.context}

@app.get("/orchestrator/documents/{document_id}")
async def get_document(
    document_id: str,
    claims: Dict[str, Any] = Depends(get_current_user_claims)
):
    workflow = await persistence.get_workflow(document_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Document workflow not found")
    return {"document_id": workflow.document_id, "state": workflow.state, "context": workflow.context}

@app.post("/orchestrator/documents/{document_id}/transition")
async def transition_document(
    document_id: str,
    req: TransitionRequest,
    claims: Dict[str, Any] = Depends(get_current_user_claims)
):
    workflow = await persistence.get_workflow(document_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Document workflow not found")
    
    if req.context:
        workflow.context.update(req.context)
        
    try:
        workflow = transition_workflow(workflow, req.trigger)
        await persistence.save_workflow(workflow)
        
        await audit_event_bus.publish_event(
            event_type=f"workflow_transition:{req.trigger}",
            document_id=document_id,
            payload={"new_state": workflow.state, "context": workflow.context}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    return {"document_id": workflow.document_id, "state": workflow.state, "context": workflow.context}

@app.post("/orchestrator/documents/{document_id}/execute-step")
async def execute_step(
    document_id: str,
    claims: Dict[str, Any] = Depends(get_current_user_claims)
):
    """
    Executes the next downstream microservice call based on the current state.
    Verifies state and dispatches requests following the single-hub-and-spoke constraint.
    """
    workflow = await persistence.get_workflow(document_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Document workflow not found")

    current_state = workflow.state
    
    # 1. State: received -> Transition to sanitizing & dispatch call
    if current_state == "received":
        sanitize_req = SanitizeRequest(
            document_id=document_id,
            raw_file_path=workflow.context.get("file_path", "")
        )
        try:
            workflow = transition_workflow(workflow, "start_sanitize")
            await persistence.save_workflow(workflow)
            
            resp = await dispatch_downstream_call(
                service_name="sanitization-agent",
                url=f"{settings.document_gateway_url}/sanitize",
                payload=sanitize_req
            )
            sanitize_resp = SanitizeResponse(**resp)
            if sanitize_resp.is_safe:
                workflow.context["clean_file_path"] = sanitize_resp.sanitized_file_path
                workflow = transition_workflow(workflow, "sanitize_success")
            else:
                workflow.context["quarantine_reason"] = sanitize_resp.quarantine_reason
                workflow = transition_workflow(workflow, "sanitize_fail")
        except Exception as e:
            logger.error(f"Downstream sanitization failed: {e}")
            raise HTTPException(status_code=502, detail=f"Downstream sanitization service error: {str(e)}")

    # 2. State: extracting -> Dispatch to extraction agent
    elif current_state == "extracting":
        extract_req = ExtractRequest(
            document_id=document_id,
            file_path=workflow.context.get("clean_file_path", "")
        )
        try:
            resp = await dispatch_downstream_call(
                service_name="extraction-agent",
                url=f"{settings.extraction_agent_url}/extract",
                payload=extract_req
            )
            extract_resp = ExtractResponse(**resp)
            workflow.context["patient_metadata"] = extract_resp.patient_metadata.model_dump() if extract_resp.patient_metadata else None
            workflow.context["extracted_data"] = extract_resp.extracted_data.model_dump()
            workflow.context["confidence_score"] = extract_resp.confidence_score
            
            workflow = transition_workflow(workflow, "extraction_success")
        except Exception as e:
            workflow = transition_workflow(workflow, "extraction_fail")
            logger.error(f"Downstream extraction failed: {e}")
            raise HTTPException(status_code=502, detail=f"Downstream extraction service error: {str(e)}")

    # 3. State: validating -> Dispatch to validation agent
    elif current_state == "validating":
        if "patient_metadata" not in workflow.context or "extracted_data" not in workflow.context:
            raise HTTPException(status_code=400, detail="Missing clinical or patient data context")
            
        validate_req = ValidateRequest(
            document_id=document_id,
            patient_metadata=workflow.context["patient_metadata"],
            extracted_data=workflow.context["extracted_data"]
        )
        try:
            resp = await dispatch_downstream_call(
                service_name="validation-agent",
                url=f"{settings.validation_agent_url}/validate",
                payload=validate_req
            )
            validate_resp = ValidateResponse(**resp)
            workflow.context["validation_issues"] = [issue.model_dump() for issue in validate_resp.issues]
            
            if validate_resp.is_valid:
                workflow = transition_workflow(workflow, "validation_success")
            elif validate_resp.requires_manual_review:
                workflow = transition_workflow(workflow, "validation_needs_review")
            else:
                workflow = transition_workflow(workflow, "validation_fail")
        except Exception as e:
            logger.error(f"Downstream validation failed: {e}")
            raise HTTPException(status_code=502, detail=f"Downstream validation service error: {str(e)}")

    # 4. State: reasoning -> Dispatch to reasoning agent
    elif current_state == "reasoning":
        reason_req = ReasonRequest(
            document_id=document_id,
            patient_id=workflow.context["patient_metadata"]["patient_id"],
            clinical_data=workflow.context["extracted_data"]
        )
        try:
            resp = await dispatch_downstream_call(
                service_name="reasoning-agent",
                url=f"{settings.reasoning_agent_url}/reason",
                payload=reason_req
            )
            reason_resp = ReasonResponse(**resp)
            workflow.context["care_gaps"] = [gap.model_dump() for gap in reason_resp.care_gaps]
            workflow.context["reasoning_summary"] = reason_resp.reasoning_summary
            
            if reason_resp.requires_human_approval:
                workflow = transition_workflow(workflow, "reasoning_needs_review")
            else:
                workflow = transition_workflow(workflow, "reasoning_success")
        except Exception as e:
            workflow = transition_workflow(workflow, "reasoning_fail")
            logger.error(f"Downstream reasoning failed: {e}")
            raise HTTPException(status_code=502, detail=f"Downstream reasoning service error: {str(e)}")

    # 5. State: writing_ehr -> Dispatch to EHR Writer
    elif current_state == "writing_ehr":
        ehr_req = EHRWriteRequest(
            document_id=document_id,
            patient_id=workflow.context["patient_metadata"]["patient_id"],
            clinical_data=workflow.context["extracted_data"],
            care_gaps=workflow.context.get("care_gaps", [])
        )
        try:
            resp = await dispatch_downstream_call(
                service_name="ehr-writer",
                url=f"{settings.ehr_writer_url}/write",
                payload=ehr_req
            )
            ehr_resp = EHRWriteResponse(**resp)
            if ehr_resp.success:
                workflow.context["fhir_resource_ids"] = ehr_resp.fhir_resource_ids
                workflow = transition_workflow(workflow, "write_ehr_success")
            else:
                workflow.context["ehr_error"] = ehr_resp.error_message
                workflow = transition_workflow(workflow, "write_ehr_fail")
        except Exception as e:
            workflow = transition_workflow(workflow, "write_ehr_fail")
            logger.error(f"Downstream EHR Write failed: {e}")
            raise HTTPException(status_code=502, detail=f"Downstream EHR write service error: {str(e)}")

    else:
        raise HTTPException(
            status_code=400,
            detail=f"No automatic transition defined for active state: {current_state}"
        )

    await persistence.save_workflow(workflow)
    return {"document_id": workflow.document_id, "state": workflow.state, "context": workflow.context}
