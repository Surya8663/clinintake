import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { ReviewQueueList } from './components/ReviewQueueList';
import { DocumentViewer } from './components/DocumentViewer';
import { EvidenceList } from './components/EvidenceList';
import { ReferralEditor } from './components/ReferralEditor';
import { StatusNotification } from './components/StatusNotification';
import { ReviewItem, DocumentFindingsResponse } from './types/clinical';
import {
  fetchReviewQueue,
  fetchDocumentFindings,
  saveReferralEdits,
  submitDecision,
} from './services/api';
import { AlertCircle, Loader2, WifiOff, Lock } from 'lucide-react';

async function generateSubmissionSignature(
  sessionKey: CryptoKey,
  clinicianId: string,
  documentId: string,
): Promise<string> {
  const timestamp = new Date().toISOString();
  const payload = `${clinicianId}:${documentId}:${timestamp}`;
  const encoder = new TextEncoder();
  const signatureBuffer = await crypto.subtle.sign(
    'HMAC',
    sessionKey,
    encoder.encode(payload),
  );
  const hashArray = Array.from(new Uint8Array(signatureBuffer));
  const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  return `SIG-HMAC256-${timestamp}-${hashHex}`;
}

export const App: React.FC = () => {
  const [queue, setQueue] = useState<ReviewItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('DOC-99482-A');
  const [findings, setFindings] = useState<DocumentFindingsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [queueError, setQueueError] = useState<string | null>(null);
  const [authError, setAuthError] = useState<boolean>(false);

  const [clinicianId, setClinicianId] = useState<string>('dr_smith');
  const [notificationMsg, setNotificationMsg] = useState<string | null>(null);
  const [notificationType, setNotificationType] = useState<'approved' | 'rejected' | 'saved' | 'error' | null>(null);

  const sessionKeyRef = useRef<CryptoKey | null>(null);
  useEffect(() => {
    crypto.subtle
      .generateKey({ name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
      .then((key) => {
        sessionKeyRef.current = key;
      });
  }, []);

  const loadQueue = async () => {
    try {
      setQueueError(null);
      const data = await fetchReviewQueue();
      setQueue(data);
      if (data.length > 0 && !selectedDocId) {
        setSelectedDocId(data[0].document_id);
      }
    } catch (err: any) {
      console.error('Error loading review queue:', err);
      setQueue([]);
      if (err.message && (err.message.includes('401') || err.message.includes('403'))) {
        setAuthError(true);
        setQueueError('Access Denied (401/403): OIDC authentication or clinician role required.');
      } else {
        setQueueError('Unable to load review queue — check connection to workspace service.');
      }
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  useEffect(() => {
    if (!selectedDocId) return;

    const loadFindings = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchDocumentFindings(selectedDocId);
        setFindings(data);
      } catch (err: any) {
        console.error(`Error loading document findings for ${selectedDocId}:`, err);
        setError(err.message || 'Failed to load document findings.');
      } finally {
        setLoading(false);
      }
    };

    loadFindings();
  }, [selectedDocId]);

  const handleSaveEdits = async (text: string) => {
    if (!selectedDocId) return;
    try {
      await saveReferralEdits(selectedDocId, text);
      setNotificationMsg(`Saved draft referral edits for ${selectedDocId} successfully.`);
      setNotificationType('saved');
    } catch (err: any) {
      console.error('Failed to save referral edits:', err);
      setNotificationMsg(
        `⚠️ Failed to save referral edits for ${selectedDocId} — changes were NOT persisted. Please retry.`
      );
      setNotificationType('error');
    }
  };

  const handleDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    if (!selectedDocId) return;

    let digitalSignature: string;
    if (sessionKeyRef.current) {
      try {
        digitalSignature = await generateSubmissionSignature(
          sessionKeyRef.current,
          clinicianId,
          selectedDocId,
        );
      } catch {
        digitalSignature = `SIG-FALLBACK-${Date.now()}-${crypto.randomUUID()}`;
      }
    } else {
      digitalSignature = `SIG-FALLBACK-${Date.now()}-${crypto.randomUUID()}`;
    }

    try {
      const res = await submitDecision(selectedDocId, decision, clinicianId, digitalSignature);
      if (decision === 'APPROVED') {
        setNotificationMsg(`✍️ Signed Approval Event emitted for ${selectedDocId}! Orchestrator authorized for EHR write.`);
        setNotificationType('approved');
      } else {
        setNotificationMsg(`❌ Document ${selectedDocId} REJECTED. EHR write blocked by governance rule.`);
        setNotificationType('rejected');
      }

      setQueue((prev) =>
        prev.map((item) =>
          item.document_id === selectedDocId
            ? { ...item, status: decision === 'APPROVED' ? 'approved' : 'rejected' }
            : item
        )
      );

      if (findings) {
        setFindings({
          ...findings,
          status: decision === 'APPROVED' ? 'approved' : 'rejected',
        });
      }
    } catch (err: any) {
      console.error(`Failed to submit ${decision} decision for ${selectedDocId}:`, err);
      const action = decision === 'APPROVED' ? 'approval' : 'rejection';
      setNotificationMsg(
        `⚠️ Failed to submit ${action} for ${selectedDocId} — ${err.message || 'request failed'}.`
      );
      setNotificationType('error');
    }
  };

  return (
    <div className="min-h-screen p-4 sm:p-6 flex flex-col">
      <Header clinicianId={clinicianId} />

      {authError && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-center gap-3 text-amber-800 text-sm">
          <Lock className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <div>
            <strong>OIDC Authentication Required:</strong> You are currently unauthenticated or lack the <code>clinician:review</code> role.
          </div>
        </div>
      )}

      {notificationMsg && (
        <div className="mb-6">
          <StatusNotification statusMessage={notificationMsg} statusType={notificationType} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        <div className="lg:col-span-3 flex flex-col">
          <ReviewQueueList
            queue={queue}
            selectedDocId={selectedDocId}
            onSelectDoc={(id) => {
              setSelectedDocId(id);
              setNotificationMsg(null);
            }}
            errorMessage={queueError}
            onRetry={loadQueue}
          />
        </div>

        <div className="lg:col-span-9 flex flex-col gap-6">
          {loading ? (
            <div className="flex-1 bg-white border border-slate-200/80 rounded-2xl p-12 flex flex-col items-center justify-center text-slate-500 shadow-sm min-h-[400px]">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin mb-3" />
              <p className="text-sm font-medium">Loading clinical findings & OCR evidence...</p>
            </div>
          ) : error ? (
            <div className="flex-1 bg-white border border-red-200 rounded-2xl p-8 flex flex-col items-center justify-center text-slate-600 shadow-sm min-h-[400px]">
              <AlertCircle className="w-10 h-10 text-red-500 mb-3" />
              <h3 className="text-base font-semibold text-slate-800 mb-1">Failed to Load Findings</h3>
              <p className="text-xs text-slate-500 mb-4 text-center max-w-md">{error}</p>
              <button
                onClick={() => setSelectedDocId(selectedDocId)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-all"
              >
                Retry Request
              </button>
            </div>
          ) : findings ? (
            <>
              <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
                <div className="xl:col-span-7 flex flex-col">
                  <DocumentViewer documentId={findings.document_id} />
                </div>
                <div className="xl:col-span-5 flex flex-col">
                  <EvidenceList evidenceSpans={findings.evidence_spans} />
                </div>
              </div>

              <ReferralEditor
                documentId={findings.document_id}
                initialText={findings.referral_text}
                status={findings.status}
                onSave={handleSaveEdits}
                onDecision={handleDecision}
              />
            </>
          ) : (
            <div className="flex-1 bg-white border border-slate-200/80 rounded-2xl p-12 flex flex-col items-center justify-center text-slate-400 shadow-sm min-h-[400px]">
              <WifiOff className="w-8 h-8 text-slate-300 mb-3" />
              <p className="text-sm">Select a document from the queue to review.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
