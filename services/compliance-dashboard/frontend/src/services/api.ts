import { AuditTrailResponse, VaultIntegrityResponse } from '../types/compliance';

// Detect whether running via Express BFF proxy (/api) or direct FastAPI
const isDirectFastAPI = window.location.port === '8019';
const API_BASE = isDirectFastAPI ? '' : '/api';

export interface AuditFilters {
  document_id?: string;
  service_name?: string;
  event_type?: string;
}

export async function fetchAuditTrail(filters?: AuditFilters): Promise<AuditTrailResponse> {
  const params = new URLSearchParams();
  if (filters?.document_id) params.set('document_id', filters.document_id);
  if (filters?.service_name) params.set('service_name', filters.service_name);
  if (filters?.event_type) params.set('event_type', filters.event_type);

  const queryString = params.toString();
  const url = `${API_BASE}/compliance/audit-trail${queryString ? `?${queryString}` : ''}`;

  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch audit trail: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchVaultIntegrity(): Promise<VaultIntegrityResponse> {
  const res = await fetch(`${API_BASE}/compliance/verify-vault`);
  if (!res.ok) {
    throw new Error(`Failed to verify vault integrity: ${res.statusText}`);
  }
  return res.json();
}
