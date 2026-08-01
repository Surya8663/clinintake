import React from 'react';
import { Activity, ShieldCheck, UserCheck, Stethoscope, Shield, BarChart3 } from 'lucide-react';

interface HeaderProps {
  clinicianId: string;
}

export const Header: React.FC<HeaderProps> = ({ clinicianId }) => {
  return (
    <header className="mb-6 space-y-4">
      {/* Top Suite Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200/80 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-800 tracking-wide uppercase text-[11px] bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            ClinIntake Suite
          </span>
          <span className="text-slate-400">|</span>
          <nav className="flex items-center gap-1">
            <a
              href={import.meta.env.VITE_WORKSPACE_URL}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-50 border border-blue-200 text-blue-700 font-medium shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-blue-500/30"
            >
              <Stethoscope className="w-3.5 h-3.5 text-blue-600" />
              <span>Clinical Workspace</span>
            </a>
            <a
              href={import.meta.env.VITE_COMPLIANCE_URL}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all focus:outline-none focus:ring-2 focus:ring-blue-500/30"
            >
              <Shield className="w-3.5 h-3.5 text-slate-500" />
              <span>Compliance Vault</span>
            </a>
            <a
              href={import.meta.env.VITE_METRICS_URL}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all focus:outline-none focus:ring-2 focus:ring-blue-500/30"
            >
              <BarChart3 className="w-3.5 h-3.5 text-slate-500" />
              <span>Pipeline Metrics</span>
            </a>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-[11px]">
            <Activity className="w-3.5 h-3.5 text-emerald-600 animate-pulse" />
            <span className="text-slate-500">Status:</span>
            <span className="font-mono font-medium text-emerald-700">API Connected</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-50 border border-slate-200 text-[11px] font-medium text-slate-700">
            <UserCheck className="w-3.5 h-3.5 text-blue-600" />
            <span className="text-slate-500">Clinician:</span>
            <strong className="text-blue-700 font-mono">{clinicianId}</strong>
          </div>
        </div>
      </div>

      {/* Primary Header Title */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-50 border border-blue-200 rounded-xl text-blue-600 shadow-sm">
            <Stethoscope className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-800">
                Human-in-the-Loop Referral Review
              </h1>
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-600" /> PRD 5.7 Governance
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-0.5">
              Review OCR spatial evidence bounding boxes, edit referral text, and sign authorization events.
            </p>
          </div>
        </div>
      </div>
    </header>
  );
};
