/** Types matching the compliance-dashboard FastAPI backend response shapes. */

export interface AuditRecord {
  event_id: string;
  document_id: string;
  service_name: string;
  event_type: string;
  hmac_signature?: string;
  created_at: string;
  metadata?: Record<string, unknown>;
}

export interface AuditTrailResponse {
  total_records: number;
  records: AuditRecord[];
  /** Present when audit-service is unreachable or RBAC forbidden */
  error?: string;
  /** "error" when audit-service is unreachable */
  status?: string;
}

export interface VaultIntegrityResponse {
  is_chain_valid?: boolean;
  is_hmac_valid?: boolean;
  total_events_verified?: number;
  status?: string;
  /** Present when vault integrity check is unavailable */
  error?: string;
}
