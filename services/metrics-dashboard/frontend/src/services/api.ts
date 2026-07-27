import { KPISummaryResponse } from '../types/metrics';

// Detect whether running via Express BFF proxy (/api) or direct FastAPI
const isDirectFastAPI = window.location.port === '8020';
const API_BASE = isDirectFastAPI ? '' : '/api';

export async function fetchPipelineKPIs(): Promise<KPISummaryResponse> {
  const res = await fetch(`${API_BASE}/metrics/kpis`);
  if (!res.ok) {
    throw new Error(`Failed to fetch pipeline KPIs: ${res.statusText}`);
  }
  return res.json();
}
