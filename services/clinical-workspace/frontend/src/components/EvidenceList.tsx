import React from 'react';
import { EvidenceSpan } from '../types/clinical';
import { Quote, Layers } from 'lucide-react';

interface EvidenceListProps {
  evidenceSpans: EvidenceSpan[];
}

export const EvidenceList: React.FC<EvidenceListProps> = ({ evidenceSpans }) => {
  return (
    <div className="glass-card p-4 flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Quote className="w-4 h-4 text-sky-400" /> Evidence Spans & Quotes
        </h2>
        <span className="text-xs text-slate-400 font-mono">
          {evidenceSpans.length} Grounded Spans
        </span>
      </div>

      <div className="space-y-3 overflow-y-auto max-h-[300px] pr-1">
        {evidenceSpans.map((span, idx) => (
          <div
            key={idx}
            className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 hover:border-sky-500/40 transition-colors"
          >
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-mono font-medium text-sky-400 uppercase tracking-wider text-[11px]">
                {span.field_name}
              </span>
              <span className="font-mono text-[10px] bg-sky-500/10 text-sky-300 border border-sky-500/20 px-1.5 py-0.5 rounded">
                BBox [{span.bbox.join(', ')}]
              </span>
            </div>
            <p className="text-xs italic text-slate-300 font-sans border-l-2 border-sky-400 pl-2.5 py-0.5">
              "{span.source_quote}"
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
