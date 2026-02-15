'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronRight, ArrowUpDown, Filter,
  User, Calendar, Stethoscope,
} from 'lucide-react';
import type { Patient, RiskLevel } from '@/types';
import { cn, formatDate, getRiskBgClass, getRiskDotClass } from '@/lib/utils';

interface PatientTableProps {
  patients: Patient[];
  total: number;
  loading?: boolean;
  onSort?: (field: string) => void;
  onFilterRisk?: (level: string) => void;
  onFilterWard?: (ward: string) => void;
  currentSort?: string;
  currentRiskFilter?: string;
  currentWardFilter?: string;
}

const riskFilters: { label: string; value: string }[] = [
  { label: 'All', value: 'all' },
  { label: 'Critical', value: 'critical' },
  { label: 'High', value: 'high' },
  { label: 'Medium', value: 'medium' },
  { label: 'Low', value: 'low' },
];

export default function PatientTable({
  patients,
  total,
  loading,
  onSort,
  onFilterRisk,
  onFilterWard,
  currentSort = 'risk_score',
  currentRiskFilter = 'all',
  currentWardFilter = 'all',
}: PatientTableProps) {
  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">Discharged Patients</h3>
          <p className="text-xs text-gray-400 mt-0.5">{total} patients total</p>
        </div>

        {/* Risk Filter Chips */}
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-gray-400" />
          {riskFilters.map((filter) => (
            <button
              key={filter.value}
              onClick={() => onFilterRisk?.(filter.value)}
              className={cn(
                currentRiskFilter === filter.value
                  ? 'filter-chip-active'
                  : 'filter-chip-inactive'
              )}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50/50">
              <th className="text-left px-5 py-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                Patient
              </th>
              <th className="text-left px-4 py-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                Diagnosis
              </th>
              <th className="text-left px-4 py-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                Ward
              </th>
              <th className="text-left px-4 py-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                <button
                  onClick={() => onSort?.('discharge_date')}
                  className="flex items-center gap-1 hover:text-gray-700"
                >
                  Discharge
                  <ArrowUpDown className="w-3 h-3" />
                </button>
              </th>
              <th className="text-left px-4 py-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                <button
                  onClick={() => onSort?.('risk_score')}
                  className="flex items-center gap-1 hover:text-gray-700"
                >
                  Risk Score
                  <ArrowUpDown className="w-3 h-3" />
                </button>
              </th>
              <th className="text-left px-4 py-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                Risk Level
              </th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [...Array(8)].map((_, i) => (
                <tr key={i} className="table-row">
                  <td colSpan={7} className="px-5 py-4">
                    <div className="skeleton h-5 rounded w-full" />
                  </td>
                </tr>
              ))
            ) : (
              <AnimatePresence>
                {patients.map((patient, idx) => (
                  <motion.tr
                    key={patient.patient_id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: idx * 0.02 }}
                    className="table-row"
                  >
                    {/* Patient */}
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          'w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold',
                          patient.risk_level === 'critical' || patient.risk_level === 'high'
                            ? 'bg-red-100 text-red-700'
                            : patient.risk_level === 'medium'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-emerald-100 text-emerald-700'
                        )}>
                          {patient.name?.split(' ').map(n => n[0]).join('').slice(0, 2)}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{patient.name}</p>
                          <p className="text-[11px] text-gray-400">
                            {patient.age}y {patient.gender} &middot; {patient.patient_id}
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* Diagnosis */}
                    <td className="px-4 py-3.5">
                      <p className="text-sm text-gray-700">{patient.diagnosis}</p>
                      <p className="text-[11px] text-gray-400">{patient.diagnosis_code}</p>
                    </td>

                    {/* Ward */}
                    <td className="px-4 py-3.5">
                      <span className="text-sm text-gray-600">{patient.ward}</span>
                    </td>

                    {/* Discharge Date */}
                    <td className="px-4 py-3.5">
                      <span className="text-sm text-gray-600">
                        {formatDate(patient.discharge_date)}
                      </span>
                    </td>

                    {/* Risk Score */}
                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={cn('h-full rounded-full transition-all duration-500', {
                              'bg-emerald-500': patient.risk_level === 'low',
                              'bg-amber-500': patient.risk_level === 'medium',
                              'bg-red-500': patient.risk_level === 'high',
                              'bg-red-600': patient.risk_level === 'critical',
                            })}
                            style={{ width: `${Math.min(patient.risk_score, 100)}%` }}
                          />
                        </div>
                        <span className={cn('text-sm font-semibold tabular-nums', {
                          'text-emerald-600': patient.risk_level === 'low',
                          'text-amber-600': patient.risk_level === 'medium',
                          'text-red-600': patient.risk_level === 'high' || patient.risk_level === 'critical',
                        })}>
                          {patient.risk_score}%
                        </span>
                      </div>
                    </td>

                    {/* Risk Badge */}
                    <td className="px-4 py-3.5">
                      <span className={cn('badge border', getRiskBgClass(patient.risk_level))}>
                        <span className={cn('w-1.5 h-1.5 rounded-full mr-1.5', getRiskDotClass(patient.risk_level))} />
                        {patient.risk_level.charAt(0).toUpperCase() + patient.risk_level.slice(1)}
                      </span>
                    </td>

                    {/* Action */}
                    <td className="px-4 py-3.5">
                      <Link
                        href={`/patients/${patient.patient_id}`}
                        className="inline-flex items-center gap-1 text-xs font-medium text-brand-600 hover:text-brand-700 transition-colors"
                      >
                        View
                        <ChevronRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
