// Asteric RiskIQ - TypeScript Type Definitions

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface Patient {
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  diagnosis: string;
  diagnosis_code: string;
  ward: string;
  chronic_conditions: string[];
  length_of_stay: number;
  discharge_date: string;
  admission_date: string;
  risk_score: number;
  risk_level: RiskLevel;
  risk_horizons: RiskHorizons;
}

export interface RiskHorizons {
  '24h': number;
  '72h': number;
  '7d': number;
  '30d': number;
}

export interface PatientDetail {
  patient_id: string;
  patient_info: PatientInfo;
  risk_assessment: RiskAssessment;
  explanation: Explanation;
  anomaly_detection: AnomalyResult;
  nlp_analysis: NLPResult;
  readmission_velocity: VelocityResult;
  similar_patients: SimilarPatient[];
  timestamp: string;
}

export interface PatientInfo {
  name: string;
  age: number;
  gender: string;
  diagnosis: string;
  diagnosis_code: string;
  ward: string;
  insurance: string;
  admission_date: string;
  discharge_date: string;
  length_of_stay: number;
  chronic_conditions: string[];
  medication_count: number;
  vitals: Vitals;
  labs: Labs;
  social_factors: SocialFactors;
  bmi: number;
  smoking_status: string;
  alcohol_use: string;
}

export interface Vitals {
  bp_systolic: number;
  bp_diastolic: number;
  heart_rate: number;
  temperature: number;
  oxygen_saturation: number;
  respiratory_rate: number;
}

export interface Labs {
  hemoglobin: number;
  wbc_count: number;
  creatinine: number;
  glucose: number;
  bun: number;
  sodium: number;
  potassium: number;
}

export interface SocialFactors {
  lives_alone: boolean;
  has_caregiver: boolean;
  transportation_access: boolean;
  housing_stable: boolean;
}

export interface RiskAssessment {
  overall_score: number;
  raw_ml_score: number;
  risk_level: RiskLevel;
  confidence: number;
  horizons: RiskHorizons;
  model_breakdown: Record<string, number>;
  nlp_modifier: number;
}

export interface RiskFactor {
  feature: string;
  display_name: string;
  shap_value: number;
  raw_value: number;
  impact: 'increases' | 'decreases';
  abs_impact: number;
}

export interface Counterfactual {
  factor: string;
  current: string;
  target: string;
  action: string;
  estimated_risk_reduction: number;
}

export interface Explanation {
  top_factors: RiskFactor[];
  natural_language: string;
  counterfactuals: Counterfactual[];
}

export interface AnomalyResult {
  is_anomaly: boolean;
  anomaly_score: number;
  anomalous_features: AnomalousFeature[];
  total_anomalous_features: number;
  alert_level: string;
}

export interface AnomalousFeature {
  feature: string;
  value: number;
  expected_range: string;
  z_score: number;
  direction: string;
  severity: string;
}

export interface NLPResult {
  risk_score_modifier: number;
  risk_keywords_found: string[];
  medium_risk_keywords: string[];
  protective_keywords_found: string[];
  medications_mentioned: string[];
  social_factors: Record<string, boolean>;
  discharge_readiness: string;
  concern_level: string;
  summary: string;
  nlp_confidence: number;
}

export interface VelocityResult {
  velocity_score: number;
  avg_days_between: number | null;
  recent_gap_days?: number;
  total_admissions?: number;
  accelerating: boolean;
  risk_amplifier?: number;
}

export interface SimilarPatient {
  similarity: number;
  patient_id: string;
  age: number;
  risk_score: number;
  was_readmitted: boolean;
  readmission_days: number | null;
}

export interface Intervention {
  id: string;
  name: string;
  description: string;
  urgency: 'immediate' | 'before_discharge' | 'post_discharge';
  priority: string;
  evidence_level: string;
  evidence_score: number;
  cost_category: string;
  rationale: string;
}

export interface Alert {
  alert_id: string;
  patient_id: string;
  patient_name: string;
  risk_score: number;
  risk_level: RiskLevel;
  alert_type: string;
  message: string;
  priority: string;
  ward: string;
  status: 'active' | 'acknowledged' | 'resolved';
  created_at: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  resolved_at: string | null;
}

export interface DashboardStats {
  total_patients: number;
  average_risk_score: number;
  median_risk_score: number;
  high_risk_count: number;
  risk_distribution: Record<RiskLevel, number>;
  ward_breakdown: Record<string, WardStats>;
  age_distribution: Record<string, number>;
  top_diagnoses: { name: string; count: number }[];
  readmission_rate: number;
  model_performance: ModelPerformance;
  timestamp: string;
}

export interface WardStats {
  count: number;
  avg_risk: number;
  high_risk_count: number;
}

export interface ModelPerformance {
  training_metrics: Record<string, Record<string, number>>;
  feature_importances: Record<string, number>;
  model_weights: Record<string, number>;
  training_timestamp: string | null;
  n_features: number;
  feature_names: string[];
}

export interface SurvivalCurvePoint {
  day: number;
  survival_probability: number;
  at_risk: number;
  events?: number;
}

export interface SurvivalData {
  curve: SurvivalCurvePoint[];
  median_survival_days: number | null;
  total_patients: number;
  total_events: number;
  event_rate: number;
  patient_risk_score: number;
  patient_risk_level: RiskLevel;
}

export interface RiskDistributionBin {
  range: string;
  count: number;
  min: number;
  max: number;
}

export interface FeatureImportance {
  feature: string;
  display_name: string;
  importance: number;
}

export interface WebSocketMessage {
  type: 'alert' | 'risk_update' | 'dashboard_refresh' | 'pong';
  data?: any;
  patient_id?: string;
  timestamp?: string;
}
