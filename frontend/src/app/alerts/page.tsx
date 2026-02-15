'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import {
  Bell, AlertTriangle, CheckCircle, Clock,
  ChevronRight, Filter, Eye,
} from 'lucide-react';
import Header from '@/components/layout/Header';
import { getAlerts, acknowledgeAlert, resolveAlert } from '@/lib/api';
import { cn, formatDateTime, getRiskBgClass } from '@/lib/utils';
import type { Alert } from '@/types';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const data = await getAlerts({
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        limit: 100,
      });
      setAlerts(data.alerts);
      setStats(data.stats);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [statusFilter, priorityFilter]);

  const handleAcknowledge = async (alertId: string) => {
    try {
      await acknowledgeAlert(alertId);
      fetchAlerts();
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleResolve = async (alertId: string) => {
    try {
      await resolveAlert(alertId);
      fetchAlerts();
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const priorityIcon = (priority: string) => {
    if (priority === 'critical') return <AlertTriangle className="w-4 h-4 text-red-600" />;
    if (priority === 'high') return <AlertTriangle className="w-4 h-4 text-orange-500" />;
    return <Bell className="w-4 h-4 text-amber-500" />;
  };

  const statusBadge = (status: string) => {
    const classes: Record<string, string> = {
      active: 'bg-red-50 text-red-700 border-red-200',
      acknowledged: 'bg-amber-50 text-amber-700 border-amber-200',
      resolved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    };
    return cn('badge border', classes[status] || 'bg-gray-50 text-gray-600');
  };

  return (
    <div className="min-h-screen bg-surface-50">
      <Header
        title="Alert Center"
        subtitle={`${stats?.active || 0} active alerts requiring attention`}
        onRefresh={fetchAlerts}
      />

      <div className="p-6 space-y-6">
        {/* Alert Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: 'Total', value: stats?.total || 0, color: 'bg-gray-50', text: 'text-gray-600', icon: Bell },
            { label: 'Active', value: stats?.active || 0, color: 'bg-red-50', text: 'text-red-600', icon: AlertTriangle },
            { label: 'Acknowledged', value: stats?.acknowledged || 0, color: 'bg-amber-50', text: 'text-amber-600', icon: Eye },
            { label: 'Resolved', value: stats?.resolved || 0, color: 'bg-emerald-50', text: 'text-emerald-600', icon: CheckCircle },
          ].map((stat, idx) => {
            const Icon = stat.icon;
            return (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="stat-card"
              >
                <div className="flex items-center gap-3">
                  <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', stat.color)}>
                    <Icon className={cn('w-5 h-5', stat.text)} />
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">{stat.label}</p>
                    <p className="text-xl font-bold text-gray-900">{stat.value}</p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-gray-400" />
            <span className="text-xs font-medium text-gray-500">Status:</span>
            {['', 'active', 'acknowledged', 'resolved'].map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={cn(
                  statusFilter === s ? 'filter-chip-active' : 'filter-chip-inactive'
                )}
              >
                {s || 'All'}
              </button>
            ))}
          </div>

          <div className="w-px h-6 bg-gray-200" />

          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500">Priority:</span>
            {['', 'critical', 'high', 'medium'].map((p) => (
              <button
                key={p}
                onClick={() => setPriorityFilter(p)}
                className={cn(
                  priorityFilter === p ? 'filter-chip-active' : 'filter-chip-inactive'
                )}
              >
                {p || 'All'}
              </button>
            ))}
          </div>
        </div>

        {/* Alert List */}
        <div className="space-y-3">
          <AnimatePresence>
            {loading ? (
              [...Array(5)].map((_, i) => (
                <div key={i} className="skeleton h-24 rounded-xl" />
              ))
            ) : alerts.length === 0 ? (
              <div className="card p-12 text-center">
                <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
                <p className="text-sm font-medium text-gray-900">No alerts matching filters</p>
                <p className="text-xs text-gray-400 mt-1">Adjust filters or check back later</p>
              </div>
            ) : (
              alerts.map((alert, idx) => (
                <motion.div
                  key={alert.alert_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ delay: idx * 0.02 }}
                  className={cn(
                    'card p-4 border-l-4 transition-all hover:shadow-card-hover',
                    alert.priority === 'critical' ? 'border-l-red-500' :
                    alert.priority === 'high' ? 'border-l-orange-500' :
                    'border-l-amber-500'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {priorityIcon(alert.priority)}
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <p className="text-sm font-semibold text-gray-900">
                            {alert.patient_name}
                          </p>
                          <span className={statusBadge(alert.status)}>
                            {alert.status}
                          </span>
                          <span className={cn('badge border', getRiskBgClass(alert.risk_level))}>
                            {alert.risk_score}%
                          </span>
                        </div>
                        <p className="text-xs text-gray-600">{alert.message}</p>
                        <div className="flex items-center gap-3 mt-2">
                          <span className="text-[10px] text-gray-400">
                            {alert.alert_id}
                          </span>
                          <span className="text-[10px] text-gray-400">
                            {alert.ward}
                          </span>
                          <span className="text-[10px] text-gray-400">
                            {formatDateTime(alert.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {alert.status === 'active' && (
                        <button
                          onClick={() => handleAcknowledge(alert.alert_id)}
                          className="btn-secondary text-xs py-1.5"
                        >
                          Acknowledge
                        </button>
                      )}
                      {alert.status === 'acknowledged' && (
                        <button
                          onClick={() => handleResolve(alert.alert_id)}
                          className="btn-primary text-xs py-1.5"
                        >
                          Resolve
                        </button>
                      )}
                      <Link
                        href={`/patients/${alert.patient_id}`}
                        className="btn-secondary p-1.5"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </Link>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
