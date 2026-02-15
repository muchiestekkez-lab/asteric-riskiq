'use client';

import { useState, useEffect, useCallback } from 'react';
import Header from '@/components/layout/Header';
import PatientTable from '@/components/dashboard/PatientTable';
import { getPatients } from '@/lib/api';
import type { Patient } from '@/types';

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('risk_score');
  const [riskFilter, setRiskFilter] = useState('all');
  const [wardFilter, setWardFilter] = useState('all');
  const [search, setSearch] = useState('');

  const fetchPatients = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getPatients({
        sort_by: sortBy,
        risk_filter: riskFilter !== 'all' ? riskFilter : undefined,
        ward_filter: wardFilter !== 'all' ? wardFilter : undefined,
        search: search || undefined,
        limit: 100,
      });
      setPatients(data.patients);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to fetch patients:', err);
    } finally {
      setLoading(false);
    }
  }, [sortBy, riskFilter, wardFilter, search]);

  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  return (
    <div className="min-h-screen bg-surface-50">
      <Header
        title="Patient Registry"
        subtitle={`${total} patients in system`}
        onSearch={setSearch}
        onRefresh={fetchPatients}
      />

      <div className="p-6">
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
      </div>
    </div>
  );
}
