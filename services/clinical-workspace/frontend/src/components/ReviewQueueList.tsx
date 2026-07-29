import React from 'react';
import { ReviewItem } from '../types/clinical';
import { FileText, CheckCircle2, XCircle, Clock } from 'lucide-react';

interface ReviewQueueListProps {
  items?: ReviewItem[];
  queue?: ReviewItem[];
  selectedDocId: string;
  onSelectDoc: (docId: string) => void;
  errorMessage?: string | null;
  onRetry?: () => Promise<void>;
}

export const ReviewQueueList: React.FC<ReviewQueueListProps> = ({
  items,
  queue,
  selectedDocId,
  onSelectDoc,
}) => {
  const displayItems = items || queue || [];
  return (
    <div className="glass-card p-4 flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200">
        <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-600" /> Review Queue
        </h2>
        <span className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-mono border border-blue-100">
          {displayItems.length} Pending
        </span>
      </div>

      <div className="space-y-2 overflow-y-auto max-h-[520px] pr-1">
        {displayItems.map((item) => {
          const isSelected = item.document_id === selectedDocId;
          return (
            <button
              key={item.document_id}
              onClick={() => onSelectDoc(item.document_id)}
              className={`w-full text-left p-3 rounded-lg border transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/40 ${
                isSelected
                  ? 'bg-blue-50 border-blue-300 text-slate-800 shadow-card-lg ring-1 ring-blue-200'
                  : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300 hover:shadow-sm'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono font-medium text-xs text-blue-700">
                  {item.document_id}
                </span>
                {item.status === 'approved' && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Approved
                  </span>
                )}
                {item.status === 'rejected' && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                    <XCircle className="w-3 h-3 text-rose-600" /> Rejected
                  </span>
                )}
                {item.status === 'awaiting_approval' && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                    <Clock className="w-3 h-3 text-amber-600" /> Review Due
                  </span>
                )}
              </div>
              <div className="text-xs text-slate-600">
                Patient: <span className="font-mono font-medium text-slate-800">{item.patient_id}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
