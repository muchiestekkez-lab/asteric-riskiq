'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, RadarChart,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from 'recharts';
import { Brain, TrendingUp, Layers, Target, Shield, Zap, AlertCircle, CheckCircle } from 'lucide-react';
import Header from '@/components/layout/Header';
import {
  getModelPerformance, getFeatureImportance, getDriftDetection,
  getSeasonalPatterns, trainModel,
} from '@/lib/api';
import { cn } from '@/lib/utils';

export default function AnalyticsPage() {
  const [modelPerf, setModelPerf] = useState<any>(null);
  const [features, setFeatures] = useState<any>(null);
  const [drift, setDrift] = useState<any>(null);
  const [seasonal, setSeasonal] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [trainResult, setTrainResult] = useState<string | null>(null);
  const [trainError, setTrainError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [perf, feat, dr, seas] = await Promise.all([
        getModelPerformance(),
        getFeatureImportance(),
        getDriftDetection(),
        getSeasonalPatterns(),
      ]);
      setModelPerf(perf);
      setFeatures(feat);
      setDrift(dr);
      setSeasonal(seas);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleTrain = async () => {
    setTraining(true);
    setTrainResult(null);
    setTrainError(null);
    try {
      const result = await trainModel();
      setTrainResult(`Model trained successfully on ${result.samples} patients. Risk scores are being recalculated.`);
      // Refresh analytics data
      await fetchData();
    } catch (err: any) {
      setTrainError(err.message || 'Training failed');
    } finally {
      setTraining(false);
    }
  };

  const notTrained = modelPerf?.message && !modelPerf?.training_metrics;

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-50">
        <Header title="Analytics" subtitle="Loading..." />
        <div className="p-6 grid grid-cols-2 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="skeleton h-72 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  // Process model metrics
  const modelMetrics = modelPerf?.training_metrics || {};
  const modelData = Object.entries(modelMetrics)
    .filter(([key]) => key !== 'ensemble')
    .map(([name, metrics]: [string, any]) => ({
      name: name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
      auc: (metrics.auc_mean * 100).toFixed(1),
      precision: (metrics.precision_mean * 100).toFixed(1),
      recall: (metrics.recall_mean * 100).toFixed(1),
    }));

  const ensembleMetrics = modelMetrics.ensemble || {};

  // Process feature importance
  const featureData = (features?.global_importances || []).slice(0, 15).map((f: any) => ({
    name: f.display_name?.length > 20 ? f.display_name.slice(0, 20) + '...' : f.display_name,
    importance: (f.importance * 100).toFixed(1),
    fullName: f.display_name,
  }));

  // Model weights for radar chart
  const radarData = Object.entries(modelPerf?.model_weights || {}).map(([name, weight]: [string, any]) => ({
    model: name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    weight: weight * 100,
    auc: modelMetrics[name] ? modelMetrics[name].auc_mean * 100 : 0,
  }));

  // Seasonal data
  const monthlyData = seasonal?.monthly || [];
  const dowData = seasonal?.day_of_week || [];

  const trainAction = (
    <button
      onClick={handleTrain}
      disabled={training}
      className="btn-primary flex items-center gap-2 text-sm"
    >
      {training ? (
        <>
          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          Training...
        </>
      ) : (
        <>
          <Zap className="w-4 h-4" />
          Train Model
        </>
      )}
    </button>
  );

  return (
    <div className="min-h-screen bg-surface-50">
      <Header
        title="Analytics & Model Intelligence"
        subtitle="ML performance, feature analysis, and drift monitoring"
        onRefresh={fetchData}
        actions={trainAction}
      />

      <div className="p-6 space-y-6">
        {/* Training messages */}
        {trainResult && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-50 border border-emerald-200">
            <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
            <p className="text-sm text-emerald-700">{trainResult}</p>
          </div>
        )}
        {trainError && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-red-50 border border-red-200">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
            <p className="text-sm text-red-700">{trainError}</p>
          </div>
        )}

        {/* Not trained notice */}
        {notTrained && (
          <div className="card p-8 text-center">
            <Brain className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">AI Model Not Yet Trained</h3>
            <p className="text-sm text-gray-500 max-w-lg mx-auto mb-4">
              Import at least 50 patients with known readmission outcomes (was_readmitted = yes/no),
              then click "Train Model" to activate the AI prediction engine.
            </p>
            <button onClick={handleTrain} disabled={training} className="btn-primary inline-flex items-center gap-2">
              <Zap className="w-4 h-4" />
              {training ? 'Training...' : 'Train Model'}
            </button>
          </div>
        )}

        {/* Top Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="stat-card">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                <Brain className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Ensemble AUC</p>
                <p className="text-xl font-bold text-gray-900">
                  {ensembleMetrics.auc ? (ensembleMetrics.auc * 100).toFixed(1) : '--'}%
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="stat-card">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center">
                <Target className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Brier Score</p>
                <p className="text-xl font-bold text-gray-900">
                  {ensembleMetrics.brier_score?.toFixed(4) || '--'}
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="stat-card">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                <Layers className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Models Active</p>
                <p className="text-xl font-bold text-gray-900">5</p>
              </div>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="stat-card">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: drift?.drift_detected ? '#fef2f2' : '#f0fdf4' }}>
                <Shield className="w-5 h-5" style={{ color: drift?.drift_detected ? '#ef4444' : '#10b981' }} />
              </div>
              <div>
                <p className="text-xs text-gray-400">Data Drift</p>
                <p className={cn('text-xl font-bold', drift?.drift_detected ? 'text-red-600' : 'text-emerald-600')}>
                  {drift?.recommendation || 'STABLE'}
                </p>
              </div>
            </div>
          </motion.div>
        </div>

        {!notTrained && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Model Performance Comparison */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card p-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Model Performance (AUC %)</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={modelData} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} domain={[60, 100]} />
                    <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', fontSize: '12px' }} />
                    <Bar dataKey="auc" name="AUC" fill="#3b82f6" radius={[6, 6, 0, 0]} maxBarSize={40} fillOpacity={0.85} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </motion.div>

            {/* Ensemble Weights Radar */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="card p-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Ensemble Weights & AUC</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#e2e8f0" />
                    <PolarAngleAxis dataKey="model" tick={{ fontSize: 10, fill: '#64748b' }} />
                    <PolarRadiusAxis tick={{ fontSize: 9, fill: '#94a3b8' }} />
                    <Radar name="Weight" dataKey="weight" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
                    <Radar name="AUC" dataKey="auc" stroke="#10b981" fill="#10b981" fillOpacity={0.15} />
                    <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', fontSize: '12px' }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </motion.div>

            {/* Feature Importance */}
            {featureData.length > 0 && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="card p-6 lg:col-span-2">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">Global Feature Importance (Top 15)</h3>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={featureData} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis type="number" tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                      <YAxis dataKey="name" type="category" tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} axisLine={false} width={160} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', fontSize: '12px' }}
                        formatter={(value: any, name: any, props: any) => [`${value}%`, props.payload.fullName]}
                      />
                      <Bar dataKey="importance" radius={[0, 6, 6, 0]} maxBarSize={18}>
                        {featureData.map((_: any, i: number) => (
                          <Cell key={i} fill={i < 5 ? '#3b82f6' : i < 10 ? '#60a5fa' : '#93c5fd'} fillOpacity={0.85} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>
            )}

            {/* Seasonal Patterns - Monthly */}
            {monthlyData.length > 0 && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="card p-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-1">Admission Patterns - Monthly</h3>
                <p className="text-xs text-gray-400 mb-4">Peak month: {seasonal?.peak_month || '-'}</p>
                <div className="h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={monthlyData} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} />
                      <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', fontSize: '12px' }} />
                      <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} maxBarSize={30} fillOpacity={0.8} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>
            )}

            {/* Seasonal Patterns - Day of Week */}
            {dowData.length > 0 && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }} className="card p-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-1">Admission Patterns - Day of Week</h3>
                <p className="text-xs text-gray-400 mb-4">Peak day: {seasonal?.peak_day || '-'}</p>
                <div className="h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dowData} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="day" tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} />
                      <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', fontSize: '12px' }} />
                      <Bar dataKey="count" fill="#06b6d4" radius={[4, 4, 0, 0]} maxBarSize={40} fillOpacity={0.8} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
