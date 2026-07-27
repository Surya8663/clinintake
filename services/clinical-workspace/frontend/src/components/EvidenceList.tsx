import React from 'react';
import { EvidenceSpan } from '../types/clinical';
import { Quote, Layers } from 'lucide-react';

interface EvidenceListProps {
  evidenceSpans: EvidenceSpan[];
}

export const EvidenceList: React.FC<EvidenceListProps> = ({ evidenceSpans }) => {
  return (
    <div className="glass-card p-4 flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200">
        <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
          <Quote className="w-4 h-4 text-blue-600" /> Evidence Spans &amp; Quotes
        </h2>
        <span className="text-xs text-slate-500 font-mono">
          {evidenceSpans.length} Grounded Spans
        </span>
      </div>

      <div className="space-y-3 overflow-y-auto max-h-[300px] pr-1">
        {evidenceSpans.map((span, idx) => (
          <div
            key={idx}
            className="p-3 rounded-lg bg-slate-50 border border-slate-200 hover:border-blue-300 transition-colors"
          >
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-mono font-medium text-blue-700 uppercase tracking-wider text-[11px]">
                {span.field_name}
              </span>
              <span className="font-mono text-[10px] bg-blue-50 text-blue-700 border border-blue-200 px-1.5 py-0.5 rounded">
                BBox [{span.bbox.join(', ')}]
              </span>
            </div>
            <p className="text-xs italic text-slate-600 font-sans border-l-2 border-blue-500 pl-2.5 py-0.5">
              &quot;{span.source_quote}&quot;
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
