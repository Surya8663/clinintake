import React from 'react';
import { Activity, ShieldCheck, UserCheck, Stethoscope } from 'lucide-react';

interface HeaderProps {
  clinicianId: string;
}

export const Header: React.FC<HeaderProps> = ({ clinicianId }) => {
  return (
    <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center pb-5 border-b border-slate-800 gap-4 mb-6">
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-sky-500/10 border border-sky-500/20 rounded-xl text-sky-400">
          <Stethoscope className="w-7 h-7" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-sky-400 via-teal-300 to-indigo-400 bg-clip-text text-transparent">
              ClinIntake — Clinical Workspace
            </h1>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/30">
              <ShieldCheck className="w-3.5 h-3.5" /> PRD 5.7 Governance
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Human-in-the-Loop Referral Review & Digital Signature Authorization
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
          <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
          <span className="text-slate-400">Status:</span>
          <span className="font-mono font-medium text-emerald-400">API Connected</span>
        </div>
        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-200">
          <UserCheck className="w-4 h-4 text-sky-400" />
          <span className="text-slate-400">Clinician:</span>
          <strong className="text-sky-300 font-mono">{clinicianId}</strong>
        </div>
      </div>
    </header>
  );
};
