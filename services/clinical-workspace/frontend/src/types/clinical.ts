export interface ReviewItem {
  document_id: string;
  patient_id: string;
  status: 'awaiting_approval' | 'approved' | 'rejected';
  created_at: string;
}

export interface EvidenceSpan {
  field_name: string;
  source_quote: string;
  bbox: [number, number, number, number]; // [x_min, y_min, x_max, y_max]
}

export interface DocumentFindingsResponse {
  document_id: string;
  patient_id: string;
  referral_text: string;
  evidence_spans: EvidenceSpan[];
  status: string;
}

export interface DecisionSubmitResponse {
  document_id: string;
  decision: 'APPROVED' | 'REJECTED';
  status: string;
  signed_event_emitted: boolean;
  message: string;
}
