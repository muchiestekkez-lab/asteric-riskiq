'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  ArrowLeft, AlertTriangle, Shield, Brain,
  FileText, Users as UsersIcon, Activity,
} from 'lucide-react';
import Header from '@/components/layout/Header';
import RiskGauge from '@/components/charts/RiskGauge';
import HorizonChart from '@/components/charts/HorizonChart';
import ModelBreakdown from '@/components/charts/ModelBreakdown';
import SurvivalCurve from '@/components/charts/SurvivalCurve';
import RiskFactors from '@/components/patient/RiskFactors';
import InterventionPanel from '@/components/patient/InterventionPanel';
import PatientInfoCard from '@/components/patient/PatientInfo';
import {
  getPatientDetail, getPatientInterventions, getPatientSurvivalCurve,
} from '@/lib/api';
import { cn, getRiskBgClass } from '@/lib/utils';
import type { PatientDetail, Intervention, SurvivalData } from '@/types';

export default function PatientDetailPage() {
  const params = useParams();
  const patientId = params.id as string;

  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [survivalData, setSurvivalData] = useState<SurvivalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'risk' | 'clinical' | 'interventions'>('risk');

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [patientData, interventionData, survival] = await Promise.all([
          getPatientDetail(patientId),
          getPatientInterventions(patientId),
          getPatientSurvivalCurve(patientId),
        ]);
        setPatient(patientData);
        setInterventions(interventionData.interventions);
        setSurvivalData(survival);
      } catch (err) {
        console.error('Failed to load patient:', err);
      } finally {
        setLoading(false);
      }
    }

    if (patientId) fetchData();
  }, [patientId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-50">
        <Header title="Loading..." />
        <div className="p-6">
          <div className="grid grid-cols-3 gap-6">
            <div className="skeleton h-96 rounded-xl" />
            <div className="skeleton h-96 rounded-xl col-span-2" />
          </div>
        </div>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="min-h-screen bg-surface-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-900">Patient not found</p>
          <Link href="/" className="text-sm text-brand-600 mt-2 inline-block">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const { patient_info: info, risk_assessment: risk, explanation, anomaly_detection, nlp_analysis } = patient;

  const tabs = [
    { id: 'risk' as const, label: 'Risk Analysis', icon: Brain },
    { id: 'clinical' as const, label: 'Clinical Details', icon: FileText },
    { id: 'interventions' as const, label: 'Interventions', icon: Shield },
  ];

  return (
    <div className="min-h-screen bg-surface-50">
      <Header
        title={info.name}
        subtitle={`${info.age}y ${info.gender} | ${info.diagnosis} | ${info.ward}`}
      />

      <div className="p-6">
        {/* Back + Patient Header */}
        <div className="flex items-center justify-between mb-6">
          <Link
            href="/"
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>

          <div className="flex items-center gap-3">
            {/* Anomaly Badge */}
            {anomaly_detection.is_anomaly && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-purple-50 border border-purple-200"
              >
                <AlertTriangle className="w-3.5 h-3.5 text-purple-600" />
                <span className="text-xs font-medium text-purple-700">Anomalous Profile</span>
              </motion.div>
            )}

            {/* Risk Badge */}
            <span className={cn('badge border text-sm px-4 py-1.5', getRiskBgClass(risk.risk_level))}>
              {risk.overall_score}% - {risk.risk_level.toUpperCase()} RISK
            </span>
          </div>
        </div>

        {/* Top Section: Gauge + Horizons + Model Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card p-6 flex flex-col items-center justify-center"
          >
            <RiskGauge score={risk.overall_score} level={risk.risk_level} size={200} />
            <div className="mt-3 text-center">
              <p className="text-xs text-gray-400">
                ML Score: {risk.raw_ml_score}% | NLP Modifier: {risk.nlp_modifier > 0 ? '+' : ''}{risk.nlp_modifier}
              </p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="card p-5"
          >
            <HorizonChart horizons={risk.horizons} />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="card p-5"
          >
            <ModelBreakdown breakdown={risk.model_breakdown} confidence={risk.confidence} />
          </motion.div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 mb-6 border-b border-gray-200">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all',
                  activeTab === tab.id
                    ? 'text-brand-600 border-brand-600'
                    : 'text-gray-500 border-transparent hover:text-gray-700'
                )}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content (2/3) */}
          <div className="lg:col-span-2 space-y-6">
            {activeTab === 'risk' && (
              <>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="card p-6"
                >
                  <RiskFactors
                    factors={explanation.top_factors}
                    naturalLanguage={explanation.natural_language}
                    counterfactuals={explanation.counterfactuals}
                  />
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="card p-6"
                >
                  <SurvivalCurve data={survivalData} />
                </motion.div>

                {/* Similar Patients */}
                {patient.similar_patients.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="card p-6"
                  >
                    <div className="flex items-center gap-2 mb-4">
                      <UsersIcon className="w-4 h-4 text-gray-400" />
                      <h4 className="text-sm font-semibold text-gray-900">Similar Patients</h4>
                    </div>
                    <div className="space-y-2">
                      {patient.similar_patients.map((sp, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-3 rounded-lg bg-gray-50"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center text-[10px] font-bold text-gray-600">
                              {idx + 1}
                            </div>
                            <div>
                              <p className="text-xs font-medium text-gray-700">{sp.patient_id}</p>
                              <p className="text-[10px] text-gray-400">
                                Age: {sp.age} | Similarity: {(sp.similarity * 100).toFixed(0)}%
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-xs font-semibold text-gray-900">{sp.risk_score}%</p>
                            <p className={cn('text-[10px] font-medium', sp.was_readmitted ? 'text-red-500' : 'text-emerald-500')}>
                              {sp.was_readmitted ? 'Readmitted' : 'Not Readmitted'}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </>
            )}

            {activeTab === 'clinical' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="card p-6"
              >
                <PatientInfoCard info={info} />
              </motion.div>
            )}

            {activeTab === 'interventions' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="card p-6"
              >
                <InterventionPanel
                  interventions={interventions}
                  riskScore={risk.overall_score}
                />
              </motion.div>
            )}
          </div>

          {/* Sidebar (1/3) */}
          <div className="space-y-4">
            {/* NLP Analysis */}
            <div className="card p-5">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Clinical Notes Analysis
              </h4>
              <div className={cn(
                'px-3 py-2 rounded-lg text-xs font-medium mb-3 border',
                nlp_analysis.concern_level === 'critical' ? 'bg-red-50 text-red-700 border-red-200' :
                nlp_analysis.concern_level === 'high' ? 'bg-red-50 text-red-600 border-red-100' :
                nlp_analysis.concern_level === 'moderate' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                'bg-emerald-50 text-emerald-700 border-emerald-200'
              )}>
                Concern Level: {nlp_analysis.concern_level.toUpperCase()}
              </div>

              <p className="text-xs text-gray-600 leading-relaxed mb-3">
                {nlp_analysis.summary}
              </p>

              {nlp_analysis.risk_keywords_found.length > 0 && (
                <div className="mb-3">
                  <p className="text-[10px] text-gray-400 font-semibold mb-1">Risk Keywords</p>
                  <div className="flex flex-wrap gap-1">
                    {nlp_analysis.risk_keywords_found.map((kw) => (
                      <span key={kw} className="px-1.5 py-0.5 text-[10px] bg-red-50 text-red-600 rounded">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {nlp_analysis.protective_keywords_found.length > 0 && (
                <div className="mb-3">
                  <p className="text-[10px] text-gray-400 font-semibold mb-1">Protective Factors</p>
                  <div className="flex flex-wrap gap-1">
                    {nlp_analysis.protective_keywords_found.map((kw) => (
                      <span key={kw} className="px-1.5 py-0.5 text-[10px] bg-emerald-50 text-emerald-600 rounded">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-2 border-t border-gray-100">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="text-gray-400">Discharge Readiness</span>
                  <span className={cn('font-semibold', {
                    'text-emerald-600': nlp_analysis.discharge_readiness === 'ready',
                    'text-amber-600': nlp_analysis.discharge_readiness === 'likely_ready',
                    'text-red-600': nlp_analysis.discharge_readiness === 'not_ready',
                    'text-gray-500': nlp_analysis.discharge_readiness === 'uncertain',
                  })}>
                    {nlp_analysis.discharge_readiness.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            {/* Readmission Velocity */}
            <div className="card p-5">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Readmission Velocity
              </h4>
              <div className="text-center py-3">
                <p className="text-3xl font-bold text-gray-900">
                  {patient.readmission_velocity.velocity_score}
                </p>
                <p className="text-xs text-gray-400 mt-1">Velocity Score</p>
              </div>
              {patient.readmission_velocity.avg_days_between !== null && (
                <div className="space-y-2 pt-3 border-t border-gray-100">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Avg. Days Between</span>
                    <span className="font-medium text-gray-700">
                      {patient.readmission_velocity.avg_days_between} days
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Accelerating</span>
                    <span className={cn('font-medium',
                      patient.readmission_velocity.accelerating ? 'text-red-600' : 'text-emerald-600'
                    )}>
                      {patient.readmission_velocity.accelerating ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Anomaly Detection */}
            {anomaly_detection.is_anomaly && (
              <div className="card p-5 border-purple-200">
                <h4 className="text-xs font-semibold text-purple-600 uppercase tracking-wider mb-3">
                  Anomaly Detection
                </h4>
                <p className="text-xs text-gray-600 mb-3">
                  This patient&apos;s profile deviates from typical patterns.
                  Anomaly score: <span className="font-bold">{anomaly_detection.anomaly_score}</span>
                </p>
                {anomaly_detection.anomalous_features.slice(0, 5).map((af) => (
                  <div key={af.feature} className="flex justify-between text-[11px] py-1 border-t border-gray-50">
                    <span className="text-gray-500">{af.feature.replace(/_/g, ' ')}</span>
                    <span className={cn('font-medium', af.severity === 'high' ? 'text-red-600' : 'text-amber-600')}>
                      {af.direction} (z={af.z_score})
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Quick Vitals */}
            <div className="card p-5">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Key Vitals
              </h4>
              <div className="grid grid-cols-2 gap-2">
                <MiniVital label="BP" value={`${info.vitals.bp_systolic}/${info.vitals.bp_diastolic}`} />
                <MiniVital label="HR" value={`${info.vitals.heart_rate} bpm`} />
                <MiniVital label="SpO2" value={`${info.vitals.oxygen_saturation}%`} />
                <MiniVital label="Temp" value={`${info.vitals.temperature}F`} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function MiniVital({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-2 rounded bg-gray-50 text-center">
      <p className="text-[10px] text-gray-400">{label}</p>
      <p className="text-xs font-semibold text-gray-900">{value}</p>
    </div>
  );
}
