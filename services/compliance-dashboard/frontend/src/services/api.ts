import { AuditTrailResponse, VaultIntegrityResponse } from '../types/compliance';

const isDirectFastAPI = window.location.port === '8019';
const API_BASE = isDirectFastAPI ? '' : '/api';

export interface AuditFilters {
  document_id?: string;
  service_name?: string;
  event_type?: string;
}

function getAuthHeaders(token?: string): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };
  const authToken = token || localStorage.getItem('clinintake_access_token');
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  return headers;
}

export async function fetchAuditTrail(filters?: AuditFilters, token?: string): Promise<AuditTrailResponse> {
  const params = new URLSearchParams();
  if (filters?.document_id) params.set('document_id', filters.document_id);
  if (filters?.service_name) params.set('service_name', filters.service_name);
  if (filters?.event_type) params.set('event_type', filters.event_type);

  const queryString = params.toString();
  const url = `${API_BASE}/compliance/audit-trail${queryString ? `?${queryString}` : ''}`;

  const res = await fetch(url, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch audit trail: ${res.statusText} (${res.status})`);
  }
  return res.json();
}

export async function fetchVaultIntegrity(token?: string): Promise<VaultIntegrityResponse> {
  const res = await fetch(`${API_BASE}/compliance/verify-vault`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error(`Failed to verify vault integrity: ${res.statusText} (${res.status})`);
  }
  return res.json();
}
