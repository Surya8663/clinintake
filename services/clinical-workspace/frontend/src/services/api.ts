import { ReviewItem, DocumentFindingsResponse, DecisionSubmitResponse } from '../types/clinical';

const isDirectFastAPI = window.location.port === '8015';
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

export async function fetchReviewQueue(token?: string): Promise<ReviewItem[]> {
  const res = await fetch(`${API_BASE}/workspace/reviews`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch review queue: ${res.statusText} (${res.status})`);
  }
  return res.json();
}

export async function fetchDocumentFindings(documentId: string, token?: string): Promise<DocumentFindingsResponse> {
  const res = await fetch(`${API_BASE}/workspace/findings/${documentId}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch findings for ${documentId}: ${res.statusText} (${res.status})`);
  }
  return res.json();
}

export async function saveReferralEdits(documentId: string, text: string, token?: string): Promise<void> {
  const res = await fetch(`${API_BASE}/workspace/referral/${documentId}`, {
    method: 'PUT',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ edited_referral_text: text })
  });
  if (!res.ok) {
    throw new Error(`Failed to save referral edits: ${res.statusText} (${res.status})`);
  }
}

export async function submitDecision(
  documentId: string,
  decision: 'APPROVED' | 'REJECTED',
  clinicianId: string,
  digitalSignature: string,
  token?: string
): Promise<DecisionSubmitResponse> {
  const res = await fetch(`${API_BASE}/workspace/decision/${documentId}`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      decision,
      clinician_id: clinicianId,
      digital_signature: digitalSignature
    })
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to submit decision: ${res.statusText} (${res.status})`);
  }
  return res.json();
}
