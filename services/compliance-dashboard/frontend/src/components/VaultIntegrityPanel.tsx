import React from 'react';
import { VaultIntegrityResponse } from '../types/compliance';
import { ShieldCheck, ShieldAlert, Loader2, Lock, Hash, FileCheck } from 'lucide-react';

interface VaultIntegrityPanelProps {
  data: VaultIntegrityResponse | null;
  loading: boolean;
  error: string | null;
}

export const VaultIntegrityPanel: React.FC<VaultIntegrityPanelProps> = ({
  data,
  loading,
  error,
}) => {
  if (loading) {
    return (
      <div className="glass-card p-6 flex items-center justify-center gap-3 text-slate-500">
        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
        <span className="text-xs font-mono">Verifying vault integrity...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-3">
          <ShieldAlert className="w-5 h-5 text-amber-600" />
          <h2 className="text-sm font-semibold text-slate-800">Vault Integrity</h2>
        </div>
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
          {error || 'Vault integrity check unavailable — audit service may be unreachable.'}
        </p>
      </div>
    );
  }

  // Handle the "unreachable" status from audit_client.py
  if (data.status === 'unreachable' || data.error) {
    return (
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-3">
          <ShieldAlert className="w-5 h-5 text-amber-600" />
          <h2 className="text-sm font-semibold text-slate-800">Vault Integrity</h2>
        </div>
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
          {data.error || 'Vault integrity verification service is currently unreachable.'}
        </p>
      </div>
    );
  }

  const chainValid = data.is_chain_valid === true;
  const hmacValid = data.is_hmac_valid === true;
  const allValid = chainValid && hmacValid;

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {allValid ? (
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
          ) : (
            <ShieldAlert className="w-5 h-5 text-rose-600" />
          )}
          <h2 className="text-sm font-semibold text-slate-800">Vault Integrity</h2>
        </div>
        <span
          className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
            allValid
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
              : 'bg-rose-50 text-rose-700 border-rose-200'
          }`}
        >
          {allValid ? 'INTACT' : 'COMPROMISED'}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Chain validity */}
        <div className={`p-3 rounded-lg border text-xs ${
          chainValid
            ? 'bg-emerald-50 border-emerald-200'
            : 'bg-rose-50 border-rose-200'
        }`}>
          <div className="flex items-center gap-1.5 mb-1">
            <Lock className={`w-3.5 h-3.5 ${chainValid ? 'text-emerald-600' : 'text-rose-600'}`} />
            <span className="font-semibold text-slate-700">Hash Chain</span>
          </div>
          <span className={`font-mono font-medium ${chainValid ? 'text-emerald-700' : 'text-rose-700'}`}>
            {chainValid ? 'Valid' : 'Invalid'}
          </span>
        </div>

        {/* HMAC validity */}
        <div className={`p-3 rounded-lg border text-xs ${
          hmacValid
            ? 'bg-emerald-50 border-emerald-200'
            : 'bg-rose-50 border-rose-200'
        }`}>
          <div className="flex items-center gap-1.5 mb-1">
            <Hash className={`w-3.5 h-3.5 ${hmacValid ? 'text-emerald-600' : 'text-rose-600'}`} />
            <span className="font-semibold text-slate-700">HMAC Signatures</span>
          </div>
          <span className={`font-mono font-medium ${hmacValid ? 'text-emerald-700' : 'text-rose-700'}`}>
            {hmacValid ? 'Valid' : 'Invalid'}
          </span>
        </div>

        {/* Events verified count */}
        {data.total_events_verified !== undefined && (
          <div className="p-3 rounded-lg border bg-blue-50 border-blue-200 text-xs">
            <div className="flex items-center gap-1.5 mb-1">
              <FileCheck className="w-3.5 h-3.5 text-blue-600" />
              <span className="font-semibold text-slate-700">Events Verified</span>
            </div>
            <span className="font-mono font-medium text-blue-700">
              {data.total_events_verified}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
