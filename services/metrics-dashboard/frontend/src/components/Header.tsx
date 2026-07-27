import React from 'react';
import { BarChart3, Activity, UserCheck, Stethoscope, Shield } from 'lucide-react';

interface HeaderProps {
  serviceStatus: 'connected' | 'error' | 'loading';
  evaluatedAt: string | null;
}

export const Header: React.FC<HeaderProps> = ({ serviceStatus, evaluatedAt }) => {
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
              href="http://localhost:3000"
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all focus:outline-none focus:ring-2 focus:ring-blue-500/30"
            >
              <Stethoscope className="w-3.5 h-3.5 text-slate-500" />
              <span>Clinical Workspace</span>
            </a>
            <a
              href="http://localhost:3001"
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all focus:outline-none focus:ring-2 focus:ring-blue-500/30"
            >
              <Shield className="w-3.5 h-3.5 text-slate-500" />
              <span>Compliance Vault</span>
            </a>
            <a
              href="http://localhost:3002"
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-50 border border-blue-200 text-blue-700 font-medium shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-blue-500/30"
            >
              <BarChart3 className="w-3.5 h-3.5 text-blue-600" />
              <span>Pipeline Metrics</span>
            </a>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-[11px]">
            <Activity className={`w-3.5 h-3.5 ${
              serviceStatus === 'connected' ? 'text-emerald-600 animate-pulse' :
              serviceStatus === 'error' ? 'text-rose-600' :
              'text-slate-400 animate-pulse'
            }`} />
            <span className="text-slate-500">Backend:</span>
            <span className={`font-mono font-medium ${
              serviceStatus === 'connected' ? 'text-emerald-700' :
              serviceStatus === 'error' ? 'text-rose-700' :
              'text-slate-500'
            }`}>
              {serviceStatus === 'connected' ? 'Connected' :
               serviceStatus === 'error' ? 'Unreachable' :
               'Checking...'}
            </span>
          </div>
          {evaluatedAt && (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-600">
              <span className="text-slate-500">Evaluated:</span>
              <span className="font-mono font-medium text-slate-800">
                {new Date(evaluatedAt).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Primary Header Title */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-blue-50 border border-blue-200 rounded-xl text-blue-600 shadow-sm">
          <BarChart3 className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-800">
            Pipeline KPI Metrics Dashboard
          </h1>
          <p className="text-xs text-slate-600 mt-0.5">
            PRD Section 13 — Extraction Accuracy, Red-Flag Sensitivity &amp; Hallucination Rate
          </p>
        </div>
      </div>
    </header>
  );
};
