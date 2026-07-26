import React from 'react';
import { ReviewItem } from '../types/clinical';
import { FileText, CheckCircle2, XCircle, Clock } from 'lucide-react';

interface ReviewQueueListProps {
  items: ReviewItem[];
  selectedDocId: string;
  onSelectDoc: (docId: string) => void;
}

export const ReviewQueueList: React.FC<ReviewQueueListProps> = ({
  items,
  selectedDocId,
  onSelectDoc,
}) => {
  return (
    <div className="glass-card p-4 flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <FileText className="w-4 h-4 text-sky-400" /> Review Queue
        </h2>
        <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
          {items.length} Pending
        </span>
      </div>

      <div className="space-y-2 overflow-y-auto max-h-[520px] pr-1">
        {items.map((item) => {
          const isSelected = item.document_id === selectedDocId;
          return (
            <button
              key={item.document_id}
              onClick={() => onSelectDoc(item.document_id)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                isSelected
                  ? 'bg-sky-500/10 border-sky-500/50 text-white shadow-lg shadow-sky-500/5'
                  : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:bg-slate-800/80 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono font-medium text-xs text-sky-400">
                  {item.document_id}
                </span>
                {item.status === 'approved' && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    <CheckCircle2 className="w-3 h-3" /> Approved
                  </span>
                )}
                {item.status === 'rejected' && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                    <XCircle className="w-3 h-3" /> Rejected
                  </span>
                )}
                {item.status === 'awaiting_approval' && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                    <Clock className="w-3 h-3" /> Review Due
                  </span>
                )}
              </div>
              <div className="text-xs text-slate-400">
                Patient: <span className="font-mono font-medium text-slate-200">{item.patient_id}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
