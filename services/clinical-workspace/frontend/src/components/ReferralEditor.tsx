import React, { useState, useEffect } from 'react';
import { Save, CheckCircle, XCircle, Edit3, Loader2 } from 'lucide-react';

interface ReferralEditorProps {
  documentId: string;
  initialText: string;
  onSaveEdits: (text: string) => Promise<void>;
  onSubmitDecision: (decision: 'APPROVED' | 'REJECTED') => Promise<void>;
  currentStatus: string;
}

export const ReferralEditor: React.FC<ReferralEditorProps> = ({
  documentId,
  initialText,
  onSaveEdits,
  onSubmitDecision,
  currentStatus,
}) => {
  const [referralText, setReferralText] = useState(initialText);
  const [isSaving, setIsSaving] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setReferralText(initialText);
  }, [initialText]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSaveEdits(referralText);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    setIsSubmitting(true);
    try {
      await onSubmitDecision(decision);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="glass-card p-4 flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Edit3 className="w-4 h-4 text-sky-400" />
          <h2 className="text-sm font-semibold text-slate-200">
            Draft Referral Letter Editor
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          <span className="text-xs font-semibold text-emerald-400">Active Review</span>
        </div>
      </div>

      <textarea
        value={referralText}
        onChange={(e) => setReferralText(e.target.value)}
        rows={12}
        className="w-full bg-slate-950/90 border border-slate-800 rounded-lg p-3 text-xs font-mono text-slate-200 focus:outline-none focus:border-sky-500/60 focus:ring-1 focus:ring-sky-500/40 resize-y leading-relaxed"
        placeholder="Enter referral draft letter text..."
      />

      <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-800/80 gap-3">
        <button
          onClick={handleSave}
          disabled={isSaving || isSubmitting}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs transition-colors disabled:opacity-50"
        >
          {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
          Save Edits
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleDecision('REJECTED')}
            disabled={isSaving || isSubmitting}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-rose-600/90 hover:bg-rose-500 text-white font-medium text-xs transition-colors border border-rose-500/30 disabled:opacity-50"
          >
            {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <XCircle className="w-3.5 h-3.5" />}
            Reject Referral
          </button>

          <button
            onClick={() => handleDecision('APPROVED')}
            disabled={isSaving || isSubmitting}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-lg shadow-emerald-600/20 transition-all border border-emerald-500/30 disabled:opacity-50"
          >
            {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
            Sign & Approve
          </button>
        </div>
      </div>
    </div>
  );
};
