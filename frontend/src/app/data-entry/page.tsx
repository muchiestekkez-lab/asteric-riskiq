'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Header from '@/components/layout/Header';
import { createPatient } from '@/lib/api';
import {
  UserPlus, User, Stethoscope, Activity, Heart, FileText,
  Home, CheckCircle, AlertCircle,
} from 'lucide-react';

const CHRONIC_OPTIONS = [
  'Diabetes', 'Hypertension', 'Heart Failure', 'COPD', 'Asthma',
  'Chronic Kidney Disease', 'Coronary Artery Disease', 'Atrial Fibrillation',
  'Depression', 'Obesity', 'Anemia', 'Liver Disease',
];

const WARDS = [
  'Cardiology', 'Pulmonology', 'Internal Medicine', 'Neurology',
  'Orthopedics', 'Surgery', 'Oncology', 'ICU', 'General',
];

const INSURANCE_TYPES = ['Medicare', 'Medicaid', 'Private', 'Self-Pay', 'Other'];
const SMOKING_OPTIONS = ['never', 'former', 'current', 'unknown'];
const ALCOHOL_OPTIONS = ['none', 'light', 'moderate', 'heavy', 'unknown'];

interface FormData {
  first_name: string;
  last_name: string;
  mrn: string;
  date_of_birth: string;
  age: string;
  gender: string;
  insurance: string;
  diagnosis_code: string;
  diagnosis_name: string;
  ward: string;
  chronic_conditions: string[];
  admission_date: string;
  discharge_date: string;
  length_of_stay: string;
  num_previous_admissions: string;
  admissions_last_6months: string;
  medication_count: string;
  missed_appointments: string;
  bp_systolic: string;
  bp_diastolic: string;
  heart_rate: string;
  temperature: string;
  oxygen_saturation: string;
  respiratory_rate: string;
  bmi: string;
  hemoglobin: string;
  wbc_count: string;
  creatinine: string;
  glucose: string;
  bun: string;
  sodium: string;
  potassium: string;
  smoking_status: string;
  alcohol_use: string;
  lives_alone: boolean;
  has_caregiver: boolean;
  transportation_access: boolean;
  housing_stable: boolean;
  clinical_notes: string;
  was_readmitted: string;
  status: string;
}

const defaultForm: FormData = {
  first_name: '', last_name: '', mrn: '', date_of_birth: '',
  age: '', gender: '', insurance: '', diagnosis_code: '', diagnosis_name: '',
  ward: '', chronic_conditions: [], admission_date: '', discharge_date: '',
  length_of_stay: '', num_previous_admissions: '0', admissions_last_6months: '0',
  medication_count: '', missed_appointments: '0',
  bp_systolic: '', bp_diastolic: '', heart_rate: '', temperature: '',
  oxygen_saturation: '', respiratory_rate: '', bmi: '',
  hemoglobin: '', wbc_count: '', creatinine: '', glucose: '',
  bun: '', sodium: '', potassium: '',
  smoking_status: 'unknown', alcohol_use: 'unknown',
  lives_alone: false, has_caregiver: true, transportation_access: true, housing_stable: true,
  clinical_notes: '', was_readmitted: '', status: 'discharged',
};

export default function DataEntryPage() {
  const [form, setForm] = useState<FormData>({ ...defaultForm });
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const set = useCallback((field: keyof FormData, value: any) => {
    setForm(prev => ({ ...prev, [field]: value }));
    setError(null);
  }, []);

  const toggleChronic = useCallback((condition: string) => {
    setForm(prev => {
      const list = prev.chronic_conditions.includes(condition)
        ? prev.chronic_conditions.filter(c => c !== condition)
        : [...prev.chronic_conditions, condition];
      return { ...prev, chronic_conditions: list };
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!form.first_name || !form.last_name) {
      setError('Patient first and last name are required');
      return;
    }

    try {
      setSaving(true);
      const payload: Record<string, any> = { ...form };
      if (payload.age) payload.age = parseInt(payload.age);
      if (payload.length_of_stay) payload.length_of_stay = parseInt(payload.length_of_stay);
      if (payload.medication_count) payload.medication_count = parseInt(payload.medication_count);
      if (payload.num_previous_admissions) payload.num_previous_admissions = parseInt(payload.num_previous_admissions);
      if (payload.admissions_last_6months) payload.admissions_last_6months = parseInt(payload.admissions_last_6months);
      if (payload.missed_appointments) payload.missed_appointments = parseInt(payload.missed_appointments);
      ['bp_systolic', 'bp_diastolic', 'heart_rate', 'temperature', 'oxygen_saturation',
        'respiratory_rate', 'bmi', 'hemoglobin', 'wbc_count', 'creatinine', 'glucose',
        'bun', 'sodium', 'potassium'].forEach(k => {
        if (payload[k]) payload[k] = parseFloat(payload[k]);
        else delete payload[k];
      });
      if (payload.was_readmitted === '') delete payload.was_readmitted;
      else payload.was_readmitted = payload.was_readmitted === 'yes';

      const result = await createPatient(payload);
      setSuccess(`Patient "${form.first_name} ${form.last_name}" added successfully. Risk scoring in progress.`);
      setForm({ ...defaultForm });

      setTimeout(() => {
        router.push(`/patients/${result.patient_id}`);
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to save patient');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-50">
      <Header title="Add Patient" subtitle="Enter patient clinical data for readmission risk assessment" />

      <div className="p-6 max-w-4xl">
        <form onSubmit={handleSubmit} className="space-y-6">

          {/* Success/Error Messages */}
          {success && (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-50 border border-emerald-200">
              <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
              <p className="text-sm text-emerald-700">{success}</p>
            </div>
          )}
          {error && (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-red-50 border border-red-200">
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Demographics */}
          <section className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <User className="w-5 h-5 text-brand-600" />
              <h3 className="text-base font-semibold text-gray-900">Patient Demographics</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">First Name *</label>
                <input className="input-field" value={form.first_name} onChange={e => set('first_name', e.target.value)} required />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Last Name *</label>
                <input className="input-field" value={form.last_name} onChange={e => set('last_name', e.target.value)} required />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">MRN</label>
                <input className="input-field" value={form.mrn} onChange={e => set('mrn', e.target.value)} placeholder="Medical Record Number" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Date of Birth</label>
                <input type="date" className="input-field" value={form.date_of_birth} onChange={e => set('date_of_birth', e.target.value)} />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Age</label>
                <input type="number" className="input-field" value={form.age} onChange={e => set('age', e.target.value)} min="0" max="120" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Gender</label>
                <select className="input-field" value={form.gender} onChange={e => set('gender', e.target.value)}>
                  <option value="">Select...</option>
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Insurance</label>
                <select className="input-field" value={form.insurance} onChange={e => set('insurance', e.target.value)}>
                  <option value="">Select...</option>
                  {INSURANCE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>
          </section>

          {/* Admission Details */}
          <section className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Stethoscope className="w-5 h-5 text-brand-600" />
              <h3 className="text-base font-semibold text-gray-900">Admission Details</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Primary Diagnosis (ICD-10)</label>
                <input className="input-field" value={form.diagnosis_code} onChange={e => set('diagnosis_code', e.target.value)} placeholder="e.g., I50.9" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-gray-600 mb-1">Diagnosis Description</label>
                <input className="input-field" value={form.diagnosis_name} onChange={e => set('diagnosis_name', e.target.value)} placeholder="e.g., Heart failure, unspecified" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Ward / Unit</label>
                <select className="input-field" value={form.ward} onChange={e => set('ward', e.target.value)}>
                  <option value="">Select...</option>
                  {WARDS.map(w => <option key={w} value={w}>{w}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Admission Date</label>
                <input type="date" className="input-field" value={form.admission_date} onChange={e => set('admission_date', e.target.value)} />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Discharge Date</label>
                <input type="date" className="input-field" value={form.discharge_date} onChange={e => set('discharge_date', e.target.value)} />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Length of Stay (days)</label>
                <input type="number" className="input-field" value={form.length_of_stay} onChange={e => set('length_of_stay', e.target.value)} min="0" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Previous Admissions (total)</label>
                <input type="number" className="input-field" value={form.num_previous_admissions} onChange={e => set('num_previous_admissions', e.target.value)} min="0" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Admissions Last 6 Months</label>
                <input type="number" className="input-field" value={form.admissions_last_6months} onChange={e => set('admissions_last_6months', e.target.value)} min="0" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Medication Count</label>
                <input type="number" className="input-field" value={form.medication_count} onChange={e => set('medication_count', e.target.value)} min="0" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Missed Appointments</label>
                <input type="number" className="input-field" value={form.missed_appointments} onChange={e => set('missed_appointments', e.target.value)} min="0" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
                <select className="input-field" value={form.status} onChange={e => set('status', e.target.value)}>
                  <option value="admitted">Admitted</option>
                  <option value="discharged">Discharged</option>
                </select>
              </div>
            </div>

            {/* Chronic Conditions */}
            <div className="mt-4">
              <label className="block text-xs font-medium text-gray-600 mb-2">Chronic Conditions</label>
              <div className="flex flex-wrap gap-2">
                {CHRONIC_OPTIONS.map(c => (
                  <button key={c} type="button" onClick={() => toggleChronic(c)}
                    className={form.chronic_conditions.includes(c) ? 'filter-chip-active' : 'filter-chip-inactive'}>
                    {c}
                  </button>
                ))}
              </div>
            </div>
          </section>

          {/* Vitals */}
          <section className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Heart className="w-5 h-5 text-brand-600" />
              <h3 className="text-base font-semibold text-gray-900">Vitals at Discharge</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">BP Systolic (mmHg)</label>
                <input type="number" className="input-field" value={form.bp_systolic} onChange={e => set('bp_systolic', e.target.value)} placeholder="120" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">BP Diastolic (mmHg)</label>
                <input type="number" className="input-field" value={form.bp_diastolic} onChange={e => set('bp_diastolic', e.target.value)} placeholder="80" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Heart Rate (bpm)</label>
                <input type="number" className="input-field" value={form.heart_rate} onChange={e => set('heart_rate', e.target.value)} placeholder="75" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Temperature (F)</label>
                <input type="number" step="0.1" className="input-field" value={form.temperature} onChange={e => set('temperature', e.target.value)} placeholder="98.6" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">SpO2 (%)</label>
                <input type="number" className="input-field" value={form.oxygen_saturation} onChange={e => set('oxygen_saturation', e.target.value)} placeholder="97" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Respiratory Rate</label>
                <input type="number" className="input-field" value={form.respiratory_rate} onChange={e => set('respiratory_rate', e.target.value)} placeholder="16" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">BMI</label>
                <input type="number" step="0.1" className="input-field" value={form.bmi} onChange={e => set('bmi', e.target.value)} placeholder="26.0" />
              </div>
            </div>
          </section>

          {/* Labs */}
          <section className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-brand-600" />
              <h3 className="text-base font-semibold text-gray-900">Lab Results</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Hemoglobin (g/dL)</label>
                <input type="number" step="0.1" className="input-field" value={form.hemoglobin} onChange={e => set('hemoglobin', e.target.value)} placeholder="13.5" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">WBC (K/uL)</label>
                <input type="number" step="0.1" className="input-field" value={form.wbc_count} onChange={e => set('wbc_count', e.target.value)} placeholder="7.5" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Creatinine (mg/dL)</label>
                <input type="number" step="0.1" className="input-field" value={form.creatinine} onChange={e => set('creatinine', e.target.value)} placeholder="1.0" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Glucose (mg/dL)</label>
                <input type="number" className="input-field" value={form.glucose} onChange={e => set('glucose', e.target.value)} placeholder="100" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">BUN (mg/dL)</label>
                <input type="number" className="input-field" value={form.bun} onChange={e => set('bun', e.target.value)} placeholder="15" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Sodium (mEq/L)</label>
                <input type="number" className="input-field" value={form.sodium} onChange={e => set('sodium', e.target.value)} placeholder="140" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Potassium (mEq/L)</label>
                <input type="number" step="0.1" className="input-field" value={form.potassium} onChange={e => set('potassium', e.target.value)} placeholder="4.2" />
              </div>
            </div>
          </section>

          {/* Social & Lifestyle */}
          <section className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Home className="w-5 h-5 text-brand-600" />
              <h3 className="text-base font-semibold text-gray-900">Social & Lifestyle Factors</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Smoking Status</label>
                <select className="input-field" value={form.smoking_status} onChange={e => set('smoking_status', e.target.value)}>
                  {SMOKING_OPTIONS.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Alcohol Use</label>
                <select className="input-field" value={form.alcohol_use} onChange={e => set('alcohol_use', e.target.value)}>
                  {ALCOHOL_OPTIONS.map(a => <option key={a} value={a}>{a.charAt(0).toUpperCase() + a.slice(1)}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
              {[
                { key: 'lives_alone' as const, label: 'Lives Alone' },
                { key: 'has_caregiver' as const, label: 'Has Caregiver' },
                { key: 'transportation_access' as const, label: 'Has Transportation' },
                { key: 'housing_stable' as const, label: 'Stable Housing' },
              ].map(({ key, label }) => (
                <label key={key} className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={form[key]} onChange={e => set(key, e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
                  <span className="text-sm text-gray-700">{label}</span>
                </label>
              ))}
            </div>
          </section>

          {/* Clinical Notes & Outcome */}
          <section className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="w-5 h-5 text-brand-600" />
              <h3 className="text-base font-semibold text-gray-900">Clinical Notes & Outcome</h3>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Clinical / Discharge Notes</label>
                <textarea className="input-field min-h-[100px]" value={form.clinical_notes} onChange={e => set('clinical_notes', e.target.value)}
                  placeholder="Enter clinical notes, discharge summary, or relevant observations. The NLP engine will analyze these for risk factors." />
              </div>
              <div className="max-w-xs">
                <label className="block text-xs font-medium text-gray-600 mb-1">Was Readmitted? (for training data)</label>
                <select className="input-field" value={form.was_readmitted} onChange={e => set('was_readmitted', e.target.value)}>
                  <option value="">Unknown / Pending</option>
                  <option value="yes">Yes - Was readmitted within 30 days</option>
                  <option value="no">No - Not readmitted</option>
                </select>
                <p className="text-[11px] text-gray-400 mt-1">
                  Setting this for 50+ patients allows AI model training.
                </p>
              </div>
            </div>
          </section>

          {/* Submit */}
          <div className="flex items-center gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  Add Patient
                </>
              )}
            </button>
            <button type="button" onClick={() => setForm({ ...defaultForm })} className="btn-secondary">
              Clear Form
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
