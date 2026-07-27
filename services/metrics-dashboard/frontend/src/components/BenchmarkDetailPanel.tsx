import React from 'react';
import { KPISummaryResponse } from '../types/metrics';
import { FileCheck, AlertCircle, CheckCircle2, FlaskConical } from 'lucide-react';

interface BenchmarkDetailPanelProps {
  data: KPISummaryResponse | null;
}

export const BenchmarkDetailPanel: React.FC<BenchmarkDetailPanelProps> = ({ data }) => {
  if (!data) return null;

  const ea = data.extraction_accuracy;
  const rf = data.red_flag_sensitivity;
  const hr = data.hallucination_rate;

  const benchmarks = [
    {
      label: 'Extraction Test Set',
      icon: <FileCheck className="w-3.5 h-3.5 text-blue-600" />,
      samples: ea.total_test_samples,
      result: `${ea.correct_fields}/${ea.total_fields} fields`,
      pass: ea.accuracy_percentage >= 90,
    },
    {
      label: 'Emergency Detection',
      icon: <AlertCircle className="w-3.5 h-3.5 text-blue-600" />,
      samples: rf.total_emergency_cases,
      result: `${rf.detected_cases}/${rf.total_emergency_cases} cases`,
      pass: rf.sensitivity_percentage >= 95,
    },
    {
      label: 'Citation Grounding',
      icon: <FlaskConical className="w-3.5 h-3.5 text-blue-600" />,
      samples: hr.total_explanations,
      result: `${hr.hallucinated_citations} hallucinated`,
      pass: hr.hallucination_rate_percentage <= 5,
    },
  ];

  return (
    <div className="glass-card p-5">
      <div className="flex items-center gap-2 mb-4">
        <CheckCircle2 className="w-4 h-4 text-blue-600" />
        <h3 className="text-sm font-semibold text-slate-800">Benchmark Evaluation Summary</h3>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {benchmarks.map((b) => (
          <div
            key={b.label}
            className={`p-3 rounded-lg border text-xs ${
              b.pass
                ? 'bg-emerald-50 border-emerald-200'
                : 'bg-amber-50 border-amber-200'
            }`}
          >
            <div className="flex items-center gap-1.5 mb-1.5">
              {b.icon}
              <span className="font-semibold text-slate-700">{b.label}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">{b.samples} samples</span>
              <span className={`font-mono font-semibold ${
                b.pass ? 'text-emerald-700' : 'text-amber-700'
              }`}>
                {b.result}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
