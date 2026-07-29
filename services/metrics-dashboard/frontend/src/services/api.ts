import { KPISummaryResponse } from '../types/metrics';

const isDirectFastAPI = window.location.port === '8020';
const API_BASE = isDirectFastAPI ? '' : '/api';

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

export async function fetchPipelineKPIs(token?: string): Promise<KPISummaryResponse> {
  const res = await fetch(`${API_BASE}/metrics/kpis`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch pipeline KPIs: ${res.statusText} (${res.status})`);
  }
  return res.json();
}
