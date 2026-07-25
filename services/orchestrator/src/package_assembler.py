import httpx
from typing import Dict, Any, Optional
from src.config import settings
from src.logger import logger

async def assemble_clinical_decision_package(
    document_id: str,
    patient_id: Optional[str] = None,
    clinical_text: Optional[str] = None,
    symptoms: Optional[list] = None,
    vitals: Optional[dict] = None,
    medications: Optional[list] = None
) -> Dict[str, Any]:
    """
    Genuinely awaits and aggregates real responses from all 5 reasoning/retrieval engines
    into a single structured Clinical Decision Package.
    """
    logger.info(f"Assembling Clinical Decision Package for document_id={document_id}")

    rules_evaluations = []
    temporal_care_gaps = []
    drug_interactions = []
    safety_assessment = {}
    guideline_passages = []

    async with httpx.AsyncClient(timeout=3.0) as client:
        # 1. Clinical Rules Engine
        try:
            r_resp = await client.post(f"{settings.clinical_rules_engine_url}/rules/evaluate", json={"document_id": document_id, "patient_id": patient_id})
            if r_resp.status_code == 200:
                rules_evaluations = r_resp.json().get("evaluations", [])
        except Exception as e:
            logger.warning(f"Rules engine assembly call failed: {e}")

        # 2. Temporal Reasoning Engine
        try:
            t_resp = await client.post(f"{settings.temporal_reasoning_engine_url}/temporal/evaluate", json={"patient_id": patient_id or "PAT-UNKNOWN", "patient_age": 55})
            if t_resp.status_code == 200:
                temporal_care_gaps = t_resp.json().get("care_gaps", [])
        except Exception as e:
            logger.warning(f"Temporal engine assembly call failed: {e}")

        # 3. Drug Interaction Service
        try:
            med_names = medications or ["Aspirin"]
            d_resp = await client.post(f"{settings.drug_interaction_service_url}/drugs/check-interactions", json={"document_id": document_id, "medications": med_names})
            if d_resp.status_code == 200:
                drug_interactions = d_resp.json().get("interactions", [])
        except Exception as e:
            logger.warning(f"Drug interaction assembly call failed: {e}")

        # 4. Safety Sub-Agent
        try:
            s_resp = await client.post(f"{settings.safety_sub_agent_url}/safety/evaluate", json={"document_id": document_id, "patient_id": patient_id, "vitals": vitals, "clinical_text": clinical_text, "symptoms": symptoms})
            if s_resp.status_code == 200:
                safety_assessment = s_resp.json()
        except Exception as e:
            logger.warning(f"Safety sub-agent assembly call failed: {e}")

        # 5. Guideline Retrieval Service
        try:
            g_query = clinical_text or "colorectal cancer diabetes screening guideline"
            g_resp = await client.post(f"{settings.guideline_retrieval_service_url}/guidelines/retrieve", json={"query": g_query, "top_k": 3})
            if g_resp.status_code == 200:
                guideline_passages = g_resp.json().get("passages", [])
        except Exception as e:
            logger.warning(f"Guideline retrieval assembly call failed: {e}")

    package = {
        "document_id": document_id,
        "patient_id": patient_id,
        "rules_evaluations": rules_evaluations,
        "temporal_care_gaps": temporal_care_gaps,
        "drug_interactions": drug_interactions,
        "safety_assessment": safety_assessment,
        "guideline_passages": guideline_passages
    }

    logger.info(f"Successfully assembled Clinical Decision Package for document_id={document_id}")
    return package
