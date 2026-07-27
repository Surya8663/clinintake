import React from 'react';
import { ShieldCheck, AlertOctagon, CheckCircle2, AlertTriangle } from 'lucide-react';

interface StatusNotificationProps {
  statusMessage: string | null;
  statusType: 'approved' | 'rejected' | 'saved' | 'error' | null;
}

export const StatusNotification: React.FC<StatusNotificationProps> = ({
  statusMessage,
  statusType,
}) => {
  if (!statusMessage || !statusType) return null;

  const isApproved = statusType === 'approved';
  const isRejected = statusType === 'rejected';
  const isError = statusType === 'error';

  return (
    <div
      className={`p-4 rounded-xl border flex items-center justify-between transition-all duration-300 shadow-card ${
        isApproved
          ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
          : isRejected
          ? 'bg-rose-50 border-rose-200 text-rose-800'
          : isError
          ? 'bg-amber-50 border-amber-200 text-amber-800'
          : 'bg-blue-50 border-blue-200 text-blue-800'
      }`}
    >
      <div className="flex items-center gap-3">
        {isApproved && <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />}
        {isRejected && <AlertOctagon className="w-5 h-5 text-rose-600 shrink-0" />}
        {isError && <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />}
        {!isApproved && !isRejected && !isError && <ShieldCheck className="w-5 h-5 text-blue-600 shrink-0" />}
        <div className="text-xs font-medium leading-relaxed">
          {statusMessage}
        </div>
      </div>

      {!isError && (
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded bg-white border border-slate-200 text-[10px] font-mono text-slate-500 shrink-0">
          <span>Status:</span>
          <span className="text-blue-700">{isApproved ? 'Confirmed' : isRejected ? 'Recorded' : 'Saved'}</span>
        </div>
      )}
    </div>
  );
};
