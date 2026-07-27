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
import { AlertCircle, Loader2, WifiOff } from 'lucide-react';

/**
 * Generate a per-submission digital signature using HMAC-SHA256.
 * Derives a unique hash from clinicianId + documentId + ISO timestamp
 * keyed by a session-bound cryptographic key generated once per app session.
 */
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
  const [selectedDocId, setSelectedDocId] = useState<string>('DOC-DEMO-001');
  const [findings, setFindings] = useState<DocumentFindingsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [queueError, setQueueError] = useState<string | null>(null);

  const [notificationMsg, setNotificationMsg] = useState<string | null>(null);
  const [notificationType, setNotificationType] = useState<'approved' | 'rejected' | 'saved' | 'error' | null>(null);

  // Session-bound HMAC key — generated once per app session, never reused across sessions
  const sessionKeyRef = useRef<CryptoKey | null>(null);
  useEffect(() => {
    crypto.subtle
      .generateKey({ name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
      .then((key) => {
        sessionKeyRef.current = key;
      });
  }, []);

  // Load review queue
  useEffect(() => {
    async function loadQueue() {
      try {
        setQueueError(null);
        const queueItems = await fetchReviewQueue();
        setQueue(queueItems);
        if (queueItems.length > 0 && !selectedDocId) {
          setSelectedDocId(queueItems[0].document_id);
        }
      } catch (err: any) {
        console.error('Failed to load queue:', err);
        setQueue([]);
        setQueueError(
          'Unable to load review queue — check connection to workspace service.'
        );
      }
    }
    loadQueue();
  }, []);

  // Load findings for selected document
  useEffect(() => {
    if (!selectedDocId) return;

    async function loadFindings() {
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
    }

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

  const handleSubmitDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    if (!selectedDocId) return;

    // Generate a real per-submission cryptographic signature
    let digitalSignature: string;
    if (sessionKeyRef.current) {
      try {
        digitalSignature = await generateSubmissionSignature(
          sessionKeyRef.current,
          'DR-SURYA-MD',
          selectedDocId,
        );
      } catch {
        digitalSignature = `SIG-FALLBACK-${Date.now()}-${crypto.randomUUID()}`;
      }
    } else {
      digitalSignature = `SIG-FALLBACK-${Date.now()}-${crypto.randomUUID()}`;
    }

    try {
      const res = await submitDecision(selectedDocId, decision, 'DR-SURYA-MD', digitalSignature);
      if (decision === 'APPROVED') {
        setNotificationMsg(`✍️ Signed Approval Event emitted for ${selectedDocId}! Orchestrator authorized for EHR write.`);
        setNotificationType('approved');
      } else {
        setNotificationMsg(`❌ Document ${selectedDocId} REJECTED. EHR write blocked by governance rule.`);
        setNotificationType('rejected');
      }

      // Only update queue/findings status AFTER confirmed server response
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
        `⚠️ Failed to submit ${action} for ${selectedDocId} — request did not reach the server. ` +
        `The document status has NOT changed. Please retry.`
      );
      setNotificationType('error');
      // Explicitly do NOT update queue or findings — the decision was not recorded
    }
  };

  return (
    <div className="min-h-screen p-4 sm:p-6 flex flex-col">
      <Header clinicianId="DR-SURYA-MD" />

      {notificationMsg && (
        <div className="mb-6">
          <StatusNotification statusMessage={notificationMsg} statusType={notificationType} />
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 flex items-center gap-3 text-xs">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        {/* Review Queue Sidebar */}
        <div className="lg:col-span-3">
          {queueError ? (
            <div className="glass-card p-6 flex flex-col items-center justify-center text-center gap-3">
              <WifiOff className="w-8 h-8 text-amber-600" />
              <p className="text-xs text-amber-700 font-medium leading-relaxed">
                {queueError}
              </p>
              <button
                onClick={() => window.location.reload()}
                className="mt-2 text-[10px] px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-700 hover:bg-amber-100 transition-colors"
              >
                Retry Connection
              </button>
            </div>
          ) : (
            <ReviewQueueList
              items={queue}
              selectedDocId={selectedDocId}
              onSelectDoc={(id) => setSelectedDocId(id)}
            />
          )}
        </div>

        {/* Main Review Area */}
        <div className="lg:col-span-9 space-y-6 flex flex-col">
          {loading ? (
            <div className="glass-card p-12 flex flex-col items-center justify-center min-h-[400px] text-slate-500 gap-3">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
              <p className="text-xs font-mono">Fetching document evidence & spatial bounding boxes...</p>
            </div>
          ) : findings ? (
            <>
              {/* Document Visual Bounding Box & Evidence Section */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <DocumentViewer
                  documentId={findings.document_id}
                  patientId={findings.patient_id}
                  evidenceSpans={findings.evidence_spans}
                />
                <EvidenceList evidenceSpans={findings.evidence_spans} />
              </div>

              {/* Referral Editor & Decision Action Panel */}
              <div className="flex-1">
                <ReferralEditor
                  documentId={findings.document_id}
                  initialText={findings.referral_text}
                  onSaveEdits={handleSaveEdits}
                  onSubmitDecision={handleSubmitDecision}
                  currentStatus={findings.status}
                />
              </div>
            </>
          ) : (
            <div className="glass-card p-12 flex flex-col items-center justify-center min-h-[400px] text-slate-500">
              <AlertCircle className="w-8 h-8 text-slate-400 mb-2" />
              <p className="text-xs">No document findings selected or document not found.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
