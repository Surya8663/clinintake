from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TYPESCRIPT_CONTRACT_CONTENT = """/**
 * AUTHORITATIVE TYPED API CONTRACTS
 * Generated automatically from packages.clinical_contracts Pydantic v2 schemas.
 * DO NOT EDIT MANUALLY.
 */

export interface BaseClinicalContract {
  schema_version: string;
  workflow_id?: string;
  document_id: string;
  trace_id: string;
  correlation_id?: string;
  idempotency_key?: string;
}

export interface ApiErrorEnvelope {
  schema_version: string;
  code: string;
  message: string;
  retryable: boolean;
  dependency?: string;
  trace_id?: string;
  document_id?: string;
}

export interface FilterScanRequest extends BaseClinicalContract {
  file_path: string;
}

export interface FilterScanResponse extends BaseClinicalContract {
  is_safe: boolean;
  threat_level: string;
  sanitized_file_path?: string;
  quarantine_reason?: string;
}

export interface OcrProcessRequest extends BaseClinicalContract {
  file_path: string;
}

export interface OcrProcessResponse extends BaseClinicalContract {
  text_content: string;
  page_count: number;
  bounding_boxes: Array<Record<string, any>>;
}

export interface ExtractRequest extends BaseClinicalContract {
  file_path: string;
  text_content?: string;
}

export interface ExtractResponse extends BaseClinicalContract {
  medications: Array<Record<string, any>>;
  diagnoses: Array<Record<string, any>>;
  labs: Array<Record<string, any>>;
  confidence_score: number;
}

export interface IdentityResolveRequest extends BaseClinicalContract {
  raw_demographics: Record<string, any>;
}

export interface IdentityResolveResponse extends BaseClinicalContract {
  patient_id: string;
  match_confidence: number;
  is_quarantined: boolean;
}

export interface SchemaValidateRequest extends BaseClinicalContract {
  clinical_data: Record<string, any>;
}

export interface SchemaValidateResponse extends BaseClinicalContract {
  is_valid: boolean;
  issues: Array<Record<string, any>>;
  requires_manual_review: boolean;
}

export interface CareGapItem {
  gap_id: string;
  title: string;
  evidence: string;
  suggested_action: string;
  status: string;
}

export interface ReferralDraftResponse extends BaseClinicalContract {
  referral_letter_text: string;
}

export interface FhirWriteTransactionRequest extends BaseClinicalContract {
  patient_id: string;
  fhir_resources: Array<Record<string, any>>;
}

export interface FhirWriteTransactionResponse extends BaseClinicalContract {
  status: string;
  fhir_bundle_id: string;
  is_duplicate: boolean;
  resource_references: string[];
}

export interface ClinicalWorkflowContext extends BaseClinicalContract {
  state: string;
  document_metadata?: Record<string, any>;
  sanitized_file_path?: string;
  patient_identity?: Record<string, any>;
  ocr_evidence?: Record<string, any>;
  extracted_clinical_data?: Record<string, any>;
  terminology_mappings: Array<Record<string, any>>;
  validation_status?: Record<string, any>;
  deterministic_outputs?: Record<string, any>;
  guideline_evidence: Array<Record<string, any>>;
  care_gaps: CareGapItem[];
  safety_state?: Record<string, any>;
  referral_draft?: Record<string, any>;
  guardrail_result?: Record<string, any>;
  clinician_approval?: Record<string, any>;
  ehr_transaction_result?: Record<string, any>;
  error_state?: ApiErrorEnvelope;
}
"""

TARGET_PATHS = [
    REPO_ROOT / "services" / "clinical-workspace" / "frontend" / "src" / "types" / "api-contracts.ts",
    REPO_ROOT / "services" / "compliance-dashboard" / "frontend" / "src" / "types" / "api-contracts.ts",
    REPO_ROOT / "services" / "metrics-dashboard" / "frontend" / "src" / "types" / "api-contracts.ts",
]


def main():
    for target in TARGET_PATHS:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(TYPESCRIPT_CONTRACT_CONTENT, encoding="utf-8")
        print(f"[OK] Generated TypeScript contract -> {target.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
