from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from packages.clinical_contracts import (
    ApiErrorEnvelope,
    CareGapExplainRequest,
    CareGapExplainResponse,
    CqlEvaluateRequest,
    ExtractRequest,
    ExtractResponse,
    FhirWriteTransactionRequest,
    FhirWriteTransactionResponse,
    FilterScanRequest,
    FilterScanResponse,
    InteractionsCheckRequest,
    SchemaValidateRequest,
    SchemaValidateResponse,
    TemporalEvaluateRequest,
)
from services.common.jwt_verifier import get_current_user_claims
from services.common.security_headers import SecurityHeadersMiddleware
from src.config import settings
from src.dispatcher import audit_event_bus, dispatch_downstream_call
from src.logger import logger
from src.persistence import persistence
from src.state_machine import DocumentWorkflow, transition_workflow


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
    context: dict[str, Any] | None = None

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception in Orchestrator", extra={"error": str(exc), "path": request.url.path})
    err_envelope = ApiErrorEnvelope(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred. Clinical workflow state preserved.",
        retryable=True,
        dependency="workflow-orchestrator"
    )
    return JSONResponse(
        status_code=500,
        content=err_envelope.model_dump()
    )

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.service_name}

@app.post("/orchestrator/documents")
async def create_document(
    req: CreateDocumentRequest,
    claims: dict[str, Any] = Depends(get_current_user_claims)
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
    claims: dict[str, Any] = Depends(get_current_user_claims)
):
    workflow = await persistence.get_workflow(document_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Document workflow not found")
    return {"document_id": workflow.document_id, "state": workflow.state, "context": workflow.context}

@app.post("/orchestrator/documents/{document_id}/transition")
async def transition_document(
    document_id: str,
    req: TransitionRequest,
    claims: dict[str, Any] = Depends(get_current_user_claims)
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

from src.lyzr_client import LyzrApiError, LyzrGovernanceViolationError, lyzr_client

PROCESSED_CALLBACK_SIGNATURES: set = set()

@app.post("/orchestrator/webhooks/lyzr-callback")
async def lyzr_webhook_callback(request: Request):
    """Webhooks callback receiver with HMAC-SHA256 verification & idempotent replay protection."""
    raw_body = await request.body()
    sig = request.headers.get("X-Lyzr-Signature", "")
    if not lyzr_client.verify_webhook_signature(raw_body, sig):
        logger.warning("[LYZR WEBHOOK] Invalid callback signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Replay Protection Check
    if sig in PROCESSED_CALLBACK_SIGNATURES:
        logger.info("[LYZR WEBHOOK REPLAY] Duplicate callback signature detected. Skipping side effects.")
        return {"status": "accepted", "replay": True}

    PROCESSED_CALLBACK_SIGNATURES.add(sig)

    data = await request.json()
    doc_id = data.get("document_id")
    if doc_id:
        workflow = await persistence.get_workflow(doc_id)
        if workflow:
            workflow.context["lyzr_last_node"] = data.get("node_id")
            workflow.context["lyzr_node_status"] = data.get("status")
            await persistence.save_workflow(workflow)
    return {"status": "accepted", "replay": False}

@app.post("/orchestrator/documents/{document_id}/execute-step")
async def execute_step(
    document_id: str,
    claims: dict[str, Any] = Depends(get_current_user_claims)
):
    """
    Authoritative workflow step runner. Starts or resumes Lyzr SuperFlow DAG execution
    and captures execution_id, session_id, and trace_id in workflow context.
    """
    workflow = await persistence.get_workflow(document_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Document workflow not found")

    # Start or attach Lyzr SuperFlow execution
    try:
        lyzr_result = lyzr_client.start_superflow_execution(
            workflow_id=settings.lyzr_superflow_id,
            document_id=document_id,
            input_payload={"file_path": workflow.context.get("file_path", ""), "state": workflow.state}
        )
        workflow.context["lyzr_execution_id"] = lyzr_result["execution_id"]
        workflow.context["lyzr_session_id"] = lyzr_result["session_id"]
        workflow.context["lyzr_trace_id"] = lyzr_result["trace_id"]
        workflow.context["lyzr_status"] = lyzr_result["status"]
        await persistence.save_workflow(workflow)
    except (LyzrApiError, LyzrGovernanceViolationError) as e:
        logger.error(f"[LYZR EXECUTION FAILURE] {e}")
        err_envelope = ApiErrorEnvelope(
            code="LYZR_SUPERFLOW_EXECUTION_FAILED",
            message=str(e),
            retryable=False,
            dependency="lyzr-superflow"
        )
        return JSONResponse(status_code=503 if isinstance(e, LyzrApiError) else 400, content=err_envelope.model_dump())

    current_state = workflow.state

    # 1. State: received -> Transition to sanitizing & dispatch to /filter/scan
    if current_state == "received":
        scan_req = FilterScanRequest(
            document_id=document_id,
            file_path=workflow.context.get("file_path", "")
        )
        try:
            workflow = transition_workflow(workflow, "start_sanitize")
            await persistence.save_workflow(workflow)

            resp = await dispatch_downstream_call(
                service_name="document-security-filter",
                url=f"{settings.document_security_filter_url}/filter/scan",
                payload=scan_req
            )
            scan_resp = FilterScanResponse(**resp)
            if scan_resp.is_safe:
                workflow.context["clean_file_path"] = scan_resp.sanitized_file_path or workflow.context.get("file_path")
                workflow = transition_workflow(workflow, "sanitize_success")
            else:
                workflow.context["quarantine_reason"] = scan_resp.quarantine_reason
                workflow = transition_workflow(workflow, "sanitize_fail")
        except Exception as e:
            logger.error(f"Downstream sanitization failed: {e}")
            raise HTTPException(status_code=502, detail=f"Downstream security filter error: {e!s}")

    # 2. State: extracting -> Dispatch to /extract
    elif current_state == "extracting":
        extract_req = ExtractRequest(
            document_id=document_id,
            file_path=workflow.context.get("clean_file_path", workflow.context.get("file_path", ""))
        )
        try:
            resp = await dispatch_downstream_call(
                service_name="extraction-agent",
                url=f"{settings.extraction_agent_url}/extract",
                payload=extract_req
            )
            extract_resp = ExtractResponse(**resp)
            workflow.context["extracted_data"] = {
                "medications": extract_resp.medications,
                "diagnoses": extract_resp.diagnoses,
                "labs": extract_resp.labs
            }
            workflow.context["confidence_score"] = extract_resp.confidence_score

            workflow = transition_workflow(workflow, "extraction_success")
        except Exception as e:
            workflow = transition_workflow(workflow, "extraction_fail")
            logger.error(f"Downstream extraction failed: {e}")
            raise HTTPException(status_code=502, detail=f"Downstream extraction service error: {e!s}")

    # 3. State: validating -> Dispatch to /validate/schema
    elif current_state == "validating":
        if "extracted_data" not in workflow.context:
            raise HTTPException(status_code=400, detail="Missing extracted clinical data context")

        validate_req = SchemaValidateRequest(
            document_id=document_id,
            clinical_data=workflow.context["extracted_data"]
        )
        try:
            resp = await dispatch_downstream_call(
                service_name="schema-validator",
                url=f"{settings.schema_validator_url}/validate/schema",
                payload=validate_req
            )
            validate_resp = SchemaValidateResponse(**resp)
            workflow.context["validation_issues"] = validate_resp.issues

            if validate_resp.is_valid:
                workflow = transition_workflow(workflow, "validation_success")
            elif validate_resp.requires_manual_review:
                workflow = transition_workflow(workflow, "validation_needs_review")
            else:
                workflow = transition_workflow(workflow, "validation_fail")
        except Exception as e:
            logger.error(f"Downstream schema validation failed: {e}")
            raise HTTPException(status_code=502, detail=f"Downstream validation service error: {e!s}")

    # 4. State: reasoning -> Orchestrate care gaps pipeline (CQL -> Temporal -> Interactions -> Guideline -> Explanation -> Draft -> Guardrail)
    elif current_state == "reasoning":
        try:
            patient_id = workflow.context.get("patient_id", "")

            # Step 4a: Rules Engine /cql/evaluate
            cql_resp = await dispatch_downstream_call(
                service_name="clinical-rules-engine",
                url=f"{settings.clinical_rules_engine_url}/cql/evaluate",
                payload=CqlEvaluateRequest(document_id=document_id, patient_id=patient_id, cql_library="uspstf_colorectal_cancer_2021")
            )

            # Step 4b: Temporal Engine /temporal/evaluate
            temporal_resp = await dispatch_downstream_call(
                service_name="temporal-reasoning-engine",
                url=f"{settings.temporal_reasoning_engine_url}/temporal/evaluate",
                payload=TemporalEvaluateRequest(document_id=document_id, patient_id=patient_id)
            )

            # Step 4c: Drug Interactions /interactions/check
            med_codes = [m.get("rxnorm_code", "") for m in workflow.context.get("extracted_data", {}).get("medications", []) if m.get("rxnorm_code")]
            interactions_resp = await dispatch_downstream_call(
                service_name="drug-interaction-service",
                url=f"{settings.drug_interaction_service_url}/interactions/check",
                payload=InteractionsCheckRequest(document_id=document_id, medication_codes=med_codes)
            )

            # Step 4d: Care Gap Explanation /care-gap/explain
            explain_resp = await dispatch_downstream_call(
                service_name="care-gap-explanation-agent",
                url=f"{settings.care_gap_explanation_agent_url}/care-gap/explain",
                payload=CareGapExplainRequest(
                    document_id=document_id,
                    patient_id=patient_id,
                    raw_care_gaps=cql_resp.get("care_gaps_identified", []),
                    guideline_evidence=[]
                )
            )
            explain_data = CareGapExplainResponse(**explain_resp)
            workflow.context["care_gaps"] = explain_data.explained_care_gaps

            workflow = transition_workflow(workflow, "reasoning_needs_review")
        except Exception as e:
            workflow = transition_workflow(workflow, "reasoning_fail")
            logger.error(f"Downstream reasoning pipeline failed: {e}")
            raise HTTPException(status_code=502, detail=f"Downstream reasoning pipeline error: {e!s}")

    # 5. State: writing_ehr -> Dispatch to /fhir/write-transaction
    elif current_state == "writing_ehr":
        target_patient_id = workflow.context.get("patient_id", "")
        ehr_req = FhirWriteTransactionRequest(
            document_id=document_id,
            patient_id=target_patient_id,
            idempotency_key=f"IDEM-WRITE-{document_id}",
            fhir_resources=[
                {"resourceType": "Patient", "id": target_patient_id}
            ]
        )
        try:
            resp = await dispatch_downstream_call(
                service_name="fhir-integration-service",
                url=f"{settings.fhir_integration_service_url}/fhir/write-transaction",
                payload=ehr_req
            )
            ehr_resp = FhirWriteTransactionResponse(**resp)
            if ehr_resp.status in ("persisted", "duplicate_skipped"):
                workflow.context["fhir_bundle_id"] = ehr_resp.fhir_bundle_id
                workflow = transition_workflow(workflow, "write_ehr_success")
            else:
                workflow = transition_workflow(workflow, "write_ehr_fail")
        except Exception as e:
            workflow = transition_workflow(workflow, "write_ehr_fail")
            logger.error(f"Downstream EHR Write failed: {e}")
            raise HTTPException(status_code=502, detail=f"Downstream EHR write service error: {e!s}")

    else:
        raise HTTPException(
            status_code=400,
            detail=f"No automatic transition defined for active state: {current_state}"
        )

    await persistence.save_workflow(workflow)
    return {"document_id": workflow.document_id, "state": workflow.state, "context": workflow.context}
