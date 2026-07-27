/**
 * Types mirroring the metrics-dashboard FastAPI backend's KPISummaryResponse.
 * These are derived directly from src/models.py — no fabricated fields.
 */

export interface ExtractionAccuracyMetric {
  total_test_samples: number;
  correct_fields: number;
  total_fields: number;
  accuracy_percentage: number;
}

export interface RedFlagSensitivityMetric {
  total_emergency_cases: number;
  detected_cases: number;
  sensitivity_percentage: number;
}

export interface HallucinationRateMetric {
  total_explanations: number;
  hallucinated_citations: number;
  hallucination_rate_percentage: number;
}

export interface KPISummaryResponse {
  extraction_accuracy: ExtractionAccuracyMetric;
  red_flag_sensitivity: RedFlagSensitivityMetric;
  hallucination_rate: HallucinationRateMetric;
  evaluated_at: string;
}
