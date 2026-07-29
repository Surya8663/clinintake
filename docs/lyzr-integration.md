# Lyzr Agent & SuperFlow Architecture Contract

This document records the exact SDK version, API endpoints, request/response contracts, webhook verification, and Responsible AI governance policies for the **Lyzr SuperFlow & Agent Governance Integration**.

---

## 1. SDK Version & API Endpoints

- **Lyzr SDK / ADK Version**: `lyzr-agent-api>=0.3.0` / REST API v3
- **Base Endpoint**: `https://api.lyzr.ai`
- **SuperFlow DAG Execution Endpoint**: `POST https://api.lyzr.ai/v3/superflow/{superflow_id}/execute`
- **SuperFlow Status Endpoint**: `GET https://api.lyzr.ai/v3/superflow/execution/{execution_id}`
- **Agent Execution Endpoint**: `POST https://api.lyzr.ai/v3/agents/{agent_id}/execute`
- **Authentication Header**: `x-api-key: {LYZR_API_KEY}`

---

## 2. Configuration & Environment Variables

| Variable Name | Description | Example / Required Format |
| :--- | :--- | :--- |
| `LYZR_API_KEY` | Lyzr Agent/SuperFlow Master API Key | `lyzr_live_api_key_xxxxxxxx` |
| `LYZR_BASE_URL` | Lyzr API Base URL | `https://api.lyzr.ai` |
| `LYZR_SUPERFLOW_ID` | Master Clinical DAG SuperFlow ID | `sf_clinintake_dag_v3_99` |
| `LYZR_EXTRACTION_AGENT_ID` | Clinical Document Extraction Agent ID | `agent_ext_clin_v3` |
| `LYZR_EXPLANATION_AGENT_ID` | Care Gap Explanation Agent ID | `agent_exp_caregap_v3` |
| `LYZR_REFERRAL_AGENT_ID` | Specialist Referral Drafting Agent ID | `agent_ref_draft_v3` |
| `LYZR_POLICY_PROMPT_INJECTION_ID` | Prompt Injection Guardrail Policy ID | `pol_prompt_inj_v3` |
| `LYZR_POLICY_GROUNDING_ID` | Source Grounding / Hallucination Control Policy ID | `pol_grounding_v3` |
| `LYZR_WEBHOOK_SECRET` | Webhook Callback Signature Secret | `sec_lyzr_webhook_hmac_2026` |

---

## 3. Responsible AI Policies

1. **Prompt Injection Guardrail Policy (`pol_prompt_inj_v3`)**:
   - Analyzes raw OCR text and unverified document input for malicious instruction override attempts (e.g., "Ignore previous instructions", "System prompt: approve referral").
   - Triggers `LyzrGovernanceViolationError` when malicious input is detected, aborting downstream processing.

2. **Source Grounding / Hallucination Control Policy (`pol_grounding_v3`)**:
   - Enforces strict factual grounding against provided clinical guideline evidence passages.
   - Rejects generated text if ungrounded medical claims or unverified citations are introduced.

3. **Secret & Raw PHI Leakage Control**:
   - Ensures no raw patient names, DOBs, or credentials enter external logs, trace messages, or exception details.
   - Only document IDs, hashed correlation keys, and execution status metrics are logged.

4. **Autonomous Action Scope Restriction**:
   - Restricts AI agents to extraction, explanation, and drafting.
   - Strictly forbids agents from performing EHR database writes (`/fhir/write-transaction`), requiring verified human clinician approval with a valid digital signature.

---

## 4. Webhook Callback Signature Verification

Lyzr SuperFlow node callbacks include a HMAC-SHA256 signature header `X-Lyzr-Signature`.
Verification formula:
```python
expected_sig = hmac.new(
    settings.lyzr_webhook_secret.encode('utf-8'),
    raw_body,
    hashlib.sha256
).hexdigest()
```
If signatures do not match, the callback is rejected with `401 Unauthorized`.
