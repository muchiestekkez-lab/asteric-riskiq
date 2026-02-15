// Asteric RiskIQ - Production API Client

import type {
  Patient, PatientDetail, DashboardStats, Alert,
  Intervention, SurvivalData, RiskDistributionBin,
  FeatureImportance,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// --- Token Management ---

const TOKEN_KEY = 'riskiq_session_token';
const HOSPITAL_KEY = 'riskiq_hospital';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string, hospital: { id: string; name: string }): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(HOSPITAL_KEY, JSON.stringify(hospital));
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(HOSPITAL_KEY);
}

export function getHospital(): { id: string; name: string } | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem(HOSPITAL_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}


// --- Core Fetch ---

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, { headers, ...options });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Session expired. Please login again.');
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}

async function fetchMultipart<T>(endpoint: string, formData: FormData): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, { method: 'POST', headers, body: formData });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== 'undefined') window.location.href = '/login';
    throw new Error('Session expired');
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}


// --- Authentication ---

export async function login(accessCode: string): Promise<{
  token: string;
  hospital_id: string;
  hospital_name: string;
  message: string;
}> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ access_code: accessCode }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(error.detail || 'Invalid access code');
  }

  const data = await res.json();
  setToken(data.token, { id: data.hospital_id, name: data.hospital_name });
  return data;
}

export async function logout(): Promise<void> {
  try {
    await fetchAPI('/api/auth/logout', { method: 'POST' });
  } catch { /* ignore */ }
  clearToken();
}

export async function verifySession(): Promise<{
  valid: boolean;
  hospital_id: string;
  hospital_name: string;
} | null> {
  const token = getToken();
  if (!token) return null;
  try {
    return await fetchAPI('/api/auth/verify');
  } catch {
    clearToken();
    return null;
  }
}


// --- Dashboard ---

export async function getDashboardStats(): Promise<DashboardStats> {
  return fetchAPI('/api/dashboard/stats');
}

export async function getRiskDistribution(): Promise<RiskDistributionBin[]> {
  return fetchAPI('/api/dashboard/risk-distribution');
}


// --- Patients ---

export async function getPatients(params?: {
  sort_by?: string;
  risk_filter?: string;
  ward_filter?: string;
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<{ patients: Patient[]; total: number; limit: number; offset: number }> {
  const query = new URLSearchParams();
  if (params?.sort_by) query.set('sort_by', params.sort_by);
  if (params?.risk_filter) query.set('risk_filter', params.risk_filter);
  if (params?.ward_filter) query.set('ward_filter', params.ward_filter);
  if (params?.search) query.set('search', params.search);
  if (params?.limit) query.set('limit', String(params.limit));
  if (params?.offset) query.set('offset', String(params.offset));
  const qs = query.toString();
  return fetchAPI(`/api/patients${qs ? `?${qs}` : ''}`);
}

export async function getPatientDetail(patientId: string): Promise<PatientDetail> {
  return fetchAPI(`/api/patients/${patientId}`);
}

export async function createPatient(data: Record<string, any>): Promise<{ patient_id: string }> {
  return fetchAPI('/api/patients', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updatePatient(patientId: string, data: Record<string, any>): Promise<any> {
  return fetchAPI(`/api/patients/${patientId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deletePatient(patientId: string): Promise<any> {
  return fetchAPI(`/api/patients/${patientId}`, { method: 'DELETE' });
}

export async function importPatientsCSV(file: File): Promise<{
  imported: number;
  errors: string[];
  total_errors: number;
  message: string;
}> {
  const formData = new FormData();
  formData.append('file', file);
  return fetchMultipart('/api/patients/import', formData);
}

export async function getPatientInterventions(patientId: string): Promise<{
  patient_id: string;
  risk_score: number;
  risk_level: string;
  interventions: Intervention[];
  total_interventions: number;
}> {
  return fetchAPI(`/api/patients/${patientId}/interventions`);
}

export async function getPatientSurvivalCurve(patientId: string): Promise<SurvivalData> {
  return fetchAPI(`/api/patients/${patientId}/survival-curve`);
}


// --- Alerts ---

export async function getAlerts(params?: {
  status?: string;
  priority?: string;
  ward?: string;
  limit?: number;
}): Promise<{ alerts: Alert[]; stats: Record<string, any> }> {
  const query = new URLSearchParams();
  if (params?.status) query.set('status', params.status);
  if (params?.priority) query.set('priority', params.priority);
  if (params?.ward) query.set('ward', params.ward);
  if (params?.limit) query.set('limit', String(params.limit));
  const qs = query.toString();
  return fetchAPI(`/api/alerts${qs ? `?${qs}` : ''}`);
}

export async function acknowledgeAlert(alertId: string): Promise<Alert> {
  return fetchAPI(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' });
}

export async function resolveAlert(alertId: string): Promise<Alert> {
  return fetchAPI(`/api/alerts/${alertId}/resolve`, { method: 'POST' });
}


// --- Analytics ---

export async function getModelPerformance(): Promise<any> {
  return fetchAPI('/api/analytics/model-performance');
}

export async function getFeatureImportance(): Promise<{ global_importances: FeatureImportance[] }> {
  return fetchAPI('/api/analytics/feature-importance');
}

export async function getDriftDetection(): Promise<any> {
  return fetchAPI('/api/analytics/drift-detection');
}

export async function getSeasonalPatterns(): Promise<any> {
  return fetchAPI('/api/analytics/seasonal-patterns');
}

export async function trainModel(): Promise<{
  status: string;
  samples: number;
  metrics: any;
}> {
  return fetchAPI('/api/model/train', { method: 'POST' });
}


// --- System ---

export async function getHealthCheck(): Promise<any> {
  return fetchAPI('/api/system/health');
}

export async function getICD10Codes(): Promise<Record<string, string>> {
  return fetchAPI('/api/system/icd10');
}
