import React from 'react';
import { ShieldCheck, AlertOctagon, CheckCircle2 } from 'lucide-react';

interface StatusNotificationProps {
  statusMessage: string | null;
  statusType: 'approved' | 'rejected' | 'saved' | null;
}

export const StatusNotification: React.FC<StatusNotificationProps> = ({
  statusMessage,
  statusType,
}) => {
  if (!statusMessage || !statusType) return null;

  const isApproved = statusType === 'approved';
  const isRejected = statusType === 'rejected';

  return (
    <div
      className={`p-4 rounded-xl border flex items-center justify-between transition-all duration-300 shadow-lg ${
        isApproved
          ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-200 shadow-emerald-950/40'
          : isRejected
          ? 'bg-rose-950/80 border-rose-500/40 text-rose-200 shadow-rose-950/40'
          : 'bg-sky-950/80 border-sky-500/40 text-sky-200 shadow-sky-950/40'
      }`}
    >
      <div className="flex items-center gap-3">
        {isApproved && <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />}
        {isRejected && <AlertOctagon className="w-5 h-5 text-rose-400 shrink-0" />}
        {!isApproved && !isRejected && <ShieldCheck className="w-5 h-5 text-sky-400 shrink-0" />}
        <div className="text-xs font-medium leading-relaxed">
          {statusMessage}
        </div>
      </div>

      <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded bg-slate-900/80 border border-slate-800 text-[10px] font-mono text-slate-400 shrink-0">
        <span>Digital Sig:</span>
        <span className="text-sky-300">SIG-ECDSA-2026-X99</span>
      </div>
    </div>
  );
};
