import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
} from 'recharts';
import { KPISummaryResponse } from '../types/metrics';
import { Loader2, PieChart as PieChartIcon, BarChart3 } from 'lucide-react';

interface TrendChartsProps {
  data: KPISummaryResponse | null;
  loading: boolean;
}

// Color tokens from the ClinIntake design system
const COLORS = {
  primary: '#2563eb',    // blue-600
  success: '#059669',    // emerald-600
  warning: '#d97706',    // amber-600
  danger: '#e11d48',     // rose-600
  muted: '#94a3b8',      // slate-400
  surface: '#f8fafc',    // slate-50
  border: '#e2e8f0',     // slate-200
};

export const TrendCharts: React.FC<TrendChartsProps> = ({ data, loading }) => {
  if (loading || !data) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card p-6 flex items-center justify-center min-h-[300px]">
          <div className="flex flex-col items-center gap-2 text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            <span className="text-xs font-mono">Loading charts...</span>
          </div>
        </div>
        <div className="glass-card p-6 flex items-center justify-center min-h-[300px]">
          <div className="flex flex-col items-center gap-2 text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            <span className="text-xs font-mono">Loading charts...</span>
          </div>
        </div>
      </div>
    );
  }

  // Build chart data from the real API response — no hardcoded numbers
  const barData = [
    {
      name: 'Extraction Accuracy',
      value: data.extraction_accuracy.accuracy_percentage,
      fill: data.extraction_accuracy.accuracy_percentage >= 90 ? COLORS.success : COLORS.warning,
    },
    {
      name: 'Red-Flag Sensitivity',
      value: data.red_flag_sensitivity.sensitivity_percentage,
      fill: data.red_flag_sensitivity.sensitivity_percentage >= 95 ? COLORS.success : COLORS.warning,
    },
    {
      name: 'Groundedness Rate',
      value: 100 - data.hallucination_rate.hallucination_rate_percentage,
      fill: data.hallucination_rate.hallucination_rate_percentage <= 5 ? COLORS.success : COLORS.warning,
    },
  ];

  // Pie chart: extraction breakdown (correct vs. incorrect fields)
  const ea = data.extraction_accuracy;
  const extractionPieData = [
    { name: 'Correct', value: ea.correct_fields, fill: COLORS.success },
    { name: 'Incorrect', value: ea.total_fields - ea.correct_fields, fill: COLORS.danger },
  ];

  // Pie chart: hallucination breakdown (grounded vs. hallucinated)
  const hr = data.hallucination_rate;
  const hallucinationPieData = [
    { name: 'Grounded', value: hr.total_explanations - hr.hallucinated_citations, fill: COLORS.success },
    { name: 'Hallucinated', value: hr.hallucinated_citations, fill: COLORS.danger },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Bar chart: KPI comparison */}
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-slate-800">KPI Performance Overview</h3>
        </div>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={barData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} unit="%" />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#334155' }} width={130} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: `1px solid ${COLORS.border}`,
                borderRadius: '8px',
                fontSize: '12px',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.07)',
              }}
              formatter={(value: number) => [`${value}%`, 'Score']}
            />
            <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={28}>
              {barData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Pie charts: detail breakdowns */}
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <PieChartIcon className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-slate-800">Detail Breakdowns</h3>
        </div>
        <div className="grid grid-cols-2 gap-4">
          {/* Extraction breakdown */}
          <div>
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider text-center mb-1">
              Field Extraction
            </p>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={extractionPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={35}
                  outerRadius={60}
                  paddingAngle={3}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {extractionPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: `1px solid ${COLORS.border}`,
                    borderRadius: '8px',
                    fontSize: '11px',
                  }}
                />
                <Legend
                  iconSize={8}
                  wrapperStyle={{ fontSize: '10px', color: '#64748b' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Hallucination breakdown */}
          <div>
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider text-center mb-1">
              Citation Grounding
            </p>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={hallucinationPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={35}
                  outerRadius={60}
                  paddingAngle={3}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {hallucinationPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: `1px solid ${COLORS.border}`,
                    borderRadius: '8px',
                    fontSize: '11px',
                  }}
                />
                <Legend
                  iconSize={8}
                  wrapperStyle={{ fontSize: '10px', color: '#64748b' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
