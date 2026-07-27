import { ReviewItem, DocumentFindingsResponse, DecisionSubmitResponse } from '../types/clinical';

// Detect whether running via Express BFF proxy (/api) or direct FastAPI (/workspace)
const isDirectFastAPI = window.location.port === '8015';
const API_BASE = isDirectFastAPI ? '' : '/api';

export async function fetchReviewQueue(): Promise<ReviewItem[]> {
  const res = await fetch(`${API_BASE}/workspace/reviews`);
  if (!res.ok) {
    throw new Error(`Failed to fetch review queue: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDocumentFindings(documentId: string): Promise<DocumentFindingsResponse> {
  const res = await fetch(`${API_BASE}/workspace/findings/${documentId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch findings for ${documentId}: ${res.statusText}`);
  }
  return res.json();
}

export async function saveReferralEdits(documentId: string, text: string): Promise<void> {
  const res = await fetch(`${API_BASE}/workspace/referral/${documentId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ edited_referral_text: text })
  });
  if (!res.ok) {
    throw new Error(`Failed to save referral edits: ${res.statusText}`);
  }
}

export async function submitDecision(
  documentId: string,
  decision: 'APPROVED' | 'REJECTED',
  clinicianId: string,
  digitalSignature: string
): Promise<DecisionSubmitResponse> {
  const res = await fetch(`${API_BASE}/workspace/decision/${documentId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Scopes': 'referral:approve,referral:read'
    },
    body: JSON.stringify({
      decision,
      clinician_id: clinicianId,
      digital_signature: digitalSignature
    })
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to submit decision: ${res.statusText}`);
  }
  return res.json();
}
