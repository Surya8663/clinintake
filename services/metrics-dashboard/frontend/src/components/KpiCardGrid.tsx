import React from 'react';
import { KPISummaryResponse } from '../types/metrics';
import {
  Target,
  ShieldAlert,
  MessageSquareWarning,
  TrendingUp,
  TrendingDown,
  Loader2,
} from 'lucide-react';

interface KpiCardGridProps {
  data: KPISummaryResponse | null;
  loading: boolean;
}

interface KpiCardProps {
  title: string;
  value: number | null;
  unit: string;
  subtitle: string;
  detail: string;
  icon: React.ReactNode;
  /** Is a higher value good (accuracy, sensitivity) or bad (hallucination rate)? */
  higherIsBetter: boolean;
  /** Threshold below which the value is "good" if higherIsBetter is false */
  threshold?: number;
}

const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  unit,
  subtitle,
  detail,
  icon,
  higherIsBetter,
  threshold = 90,
}) => {
  const isGood =
    value === null
      ? null
      : higherIsBetter
      ? value >= threshold
      : value <= (100 - threshold);

  return (
    <div className="glass-card p-5 flex flex-col transition-all">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {icon}
          <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
            {title}
          </h3>
        </div>
        {value !== null && (
          isGood ? (
            <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              <TrendingUp className="w-3 h-3 text-emerald-600" /> On Target
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
              <TrendingDown className="w-3 h-3 text-amber-600" /> Needs Attention
            </span>
          )
        )}
      </div>

      {value !== null ? (
        <>
          <div className={`text-4xl font-bold font-mono mb-1 ${
            isGood ? 'text-emerald-700' : 'text-amber-700'
          }`}>
            {value}{unit}
          </div>
          <p className="text-xs text-slate-700 font-medium">{subtitle}</p>
          <p className="text-[10px] text-slate-500 mt-1">{detail}</p>
        </>
      ) : (
        <div className="flex items-center gap-2 py-4 text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
          <span className="text-xs font-mono">Loading metrics...</span>
        </div>
      )}
    </div>
  );
};

export const KpiCardGrid: React.FC<KpiCardGridProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <KpiCard
          title="Extraction Accuracy"
          value={null}
          unit="%"
          subtitle=""
          detail=""
          icon={<Target className="w-4 h-4 text-blue-600" />}
          higherIsBetter={true}
        />
        <KpiCard
          title="Red-Flag Sensitivity"
          value={null}
          unit="%"
          subtitle=""
          detail=""
          icon={<ShieldAlert className="w-4 h-4 text-blue-600" />}
          higherIsBetter={true}
        />
        <KpiCard
          title="Hallucination Rate"
          value={null}
          unit="%"
          subtitle=""
          detail=""
          icon={<MessageSquareWarning className="w-4 h-4 text-blue-600" />}
          higherIsBetter={false}
        />
      </div>
    );
  }

  if (!data) return null;

  const ea = data.extraction_accuracy;
  const rf = data.red_flag_sensitivity;
  const hr = data.hallucination_rate;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <KpiCard
        title="Extraction Accuracy"
        value={ea.accuracy_percentage}
        unit="%"
        subtitle={`${ea.correct_fields} / ${ea.total_fields} fields correct`}
        detail={`Evaluated against ${ea.total_test_samples} labeled clinical document test samples`}
        icon={<Target className="w-4 h-4 text-blue-600" />}
        higherIsBetter={true}
        threshold={90}
      />
      <KpiCard
        title="Red-Flag Sensitivity"
        value={rf.sensitivity_percentage}
        unit="%"
        subtitle={`${rf.detected_cases} / ${rf.total_emergency_cases} emergencies detected`}
        detail="Sepsis, stroke, anaphylaxis & chest pain detection against benchmark cases"
        icon={<ShieldAlert className="w-4 h-4 text-blue-600" />}
        higherIsBetter={true}
        threshold={95}
      />
      <KpiCard
        title="Hallucination Rate"
        value={hr.hallucination_rate_percentage}
        unit="%"
        subtitle={`${hr.hallucinated_citations} / ${hr.total_explanations} citations ungrounded`}
        detail="Computed from quote-grounding verification against source documents"
        icon={<MessageSquareWarning className="w-4 h-4 text-blue-600" />}
        higherIsBetter={false}
        threshold={95}
      />
    </div>
  );
};
