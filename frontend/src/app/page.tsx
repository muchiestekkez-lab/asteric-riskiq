'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import Header from '@/components/layout/Header';
import StatsCards from '@/components/dashboard/StatsCards';
import PatientTable from '@/components/dashboard/PatientTable';
import RiskDistribution from '@/components/dashboard/RiskDistribution';
import { getDashboardStats, getPatients, getRiskDistribution } from '@/lib/api';
import type { DashboardStats, Patient, RiskDistributionBin } from '@/types';
import { UserPlus, Upload, Brain } from 'lucide-react';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [distribution, setDistribution] = useState<RiskDistributionBin[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('risk_score');
  const [riskFilter, setRiskFilter] = useState('all');
  const [wardFilter, setWardFilter] = useState('all');
  const [search, setSearch] = useState('');

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [statsData, patientsData, distData] = await Promise.all([
        getDashboardStats(),
        getPatients({
          sort_by: sortBy,
          risk_filter: riskFilter !== 'all' ? riskFilter : undefined,
          ward_filter: wardFilter !== 'all' ? wardFilter : undefined,
          search: search || undefined,
          limit: 25,
        }),
        getRiskDistribution(),
      ]);

      setStats(statsData);
      setPatients(patientsData.patients);
      setTotal(patientsData.total);
      setDistribution(distData);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, [sortBy, riskFilter, wardFilter, search]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSearch = useCallback((query: string) => {
    setSearch(query);
  }, []);

  const isEmpty = !loading && total === 0 && !search;

  return (
    <div className="min-h-screen bg-surface-50">
      <Header
        title="Risk Dashboard"
        subtitle={
          stats
            ? stats.total_patients > 0
              ? `${stats.high_risk_count} high-risk patients requiring attention`
              : 'Add patients to begin risk assessment'
            : 'Loading...'
        }
        onSearch={total > 0 ? handleSearch : undefined}
        onRefresh={fetchData}
      />

      <div className="p-6 space-y-6">
        {/* Stats Cards */}
        <StatsCards stats={stats} />

        {isEmpty ? (
          /* Empty State - Getting Started */
          <div className="card p-10 text-center">
            <Brain className="w-14 h-14 text-gray-200 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Welcome to Asteric RiskIQ</h3>
            <p className="text-sm text-gray-500 max-w-md mx-auto mb-6">
              Start by adding patient records. You can enter patients manually or import from a CSV file.
              Once you have 50+ patients with known outcomes, train the AI model to activate predictions.
            </p>
            <div className="flex items-center justify-center gap-3">
              <Link href="/data-entry" className="btn-primary inline-flex items-center gap-2">
                <UserPlus className="w-4 h-4" />
                Add Patient
              </Link>
              <Link href="/import" className="btn-secondary inline-flex items-center gap-2">
                <Upload className="w-4 h-4" />
                Import CSV
              </Link>
            </div>
          </div>
        ) : (
          <>
            {/* Risk Distribution Charts */}
            <RiskDistribution stats={stats} distribution={distribution} />

            {/* Patient Table */}
            <PatientTable
              patients={patients}
              total={total}
              loading={loading}
              onSort={setSortBy}
              onFilterRisk={setRiskFilter}
              onFilterWard={setWardFilter}
              currentSort={sortBy}
              currentRiskFilter={riskFilter}
              currentWardFilter={wardFilter}
            />
          </>
        )}
      </div>
    </div>
  );
}
