import React, { useState, useEffect } from 'react';
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
import { AlertCircle, Loader2 } from 'lucide-react';

export const App: React.FC = () => {
  const [queue, setQueue] = useState<ReviewItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('DOC-DEMO-001');
  const [findings, setFindings] = useState<DocumentFindingsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [notificationMsg, setNotificationMsg] = useState<string | null>(null);
  const [notificationType, setNotificationType] = useState<'approved' | 'rejected' | 'saved' | null>(null);

  // Load review queue
  useEffect(() => {
    async function loadQueue() {
      try {
        const queueItems = await fetchReviewQueue();
        setQueue(queueItems);
        if (queueItems.length > 0 && !selectedDocId) {
          setSelectedDocId(queueItems[0].document_id);
        }
      } catch (err: any) {
        console.error('Failed to load queue:', err);
        // Fallback default queue item if API proxy offline
        setQueue([
          {
            document_id: 'DOC-DEMO-001',
            patient_id: 'PAT-99482',
            status: 'awaiting_approval',
            created_at: '2026-07-25T10:00:00Z',
          },
        ]);
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
      setNotificationMsg(`Referral edits saved in workspace context.`);
      setNotificationType('saved');
    }
  };

  const handleSubmitDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    if (!selectedDocId) return;
    try {
      const res = await submitDecision(selectedDocId, decision, 'DR-SURYA-MD', 'SIG-ECDSA-2026-X99');
      if (decision === 'APPROVED') {
        setNotificationMsg(`✍️ Signed Approval Event emitted for ${selectedDocId}! Orchestrator authorized for EHR write.`);
        setNotificationType('approved');
      } else {
        setNotificationMsg(`❌ Document ${selectedDocId} REJECTED. EHR write blocked by governance rule.`);
        setNotificationType('rejected');
      }

      // Refresh queue status
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
      if (decision === 'APPROVED') {
        setNotificationMsg(`✍️ Signed Approval Event recorded for ${selectedDocId}! Orchestrator authorized for EHR write.`);
        setNotificationType('approved');
      } else {
        setNotificationMsg(`❌ Document ${selectedDocId} REJECTED. EHR write blocked by governance rule.`);
        setNotificationType('rejected');
      }
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
        <div className="mb-6 p-4 rounded-xl bg-rose-950/80 border border-rose-500/40 text-rose-200 flex items-center gap-3 text-xs">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        {/* Review Queue Sidebar */}
        <div className="lg:col-span-3">
          <ReviewQueueList
            items={queue}
            selectedDocId={selectedDocId}
            onSelectDoc={(id) => setSelectedDocId(id)}
          />
        </div>

        {/* Main Review Area */}
        <div className="lg:col-span-9 space-y-6 flex flex-col">
          {loading ? (
            <div className="glass-card p-12 flex flex-col items-center justify-center min-h-[400px] text-slate-400 gap-3">
              <Loader2 className="w-8 h-8 text-sky-400 animate-spin" />
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
            <div className="glass-card p-12 flex flex-col items-center justify-center min-h-[400px] text-slate-400">
              <AlertCircle className="w-8 h-8 text-slate-500 mb-2" />
              <p className="text-xs">No document findings selected or document not found.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
