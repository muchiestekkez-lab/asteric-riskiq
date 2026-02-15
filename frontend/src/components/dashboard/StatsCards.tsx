'use client';

import { motion } from 'framer-motion';
import {
  Users, AlertTriangle, Activity, TrendingUp,
  Heart, ShieldAlert, Clock, BarChart,
} from 'lucide-react';
import type { DashboardStats } from '@/types';

interface StatsCardsProps {
  stats: DashboardStats | null;
}

export default function StatsCards({ stats }: StatsCardsProps) {
  if (!stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="stat-card h-28 skeleton rounded-xl" />
        ))}
      </div>
    );
  }

  const cards = [
    {
      label: 'Total Patients',
      value: stats.total_patients.toLocaleString(),
      icon: Users,
      color: 'from-blue-500 to-blue-600',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600',
      change: null,
    },
    {
      label: 'High Risk',
      value: stats.high_risk_count.toString(),
      icon: ShieldAlert,
      color: 'from-red-500 to-red-600',
      bgColor: 'bg-red-50',
      textColor: 'text-red-600',
      change: `${((stats.high_risk_count / stats.total_patients) * 100).toFixed(1)}% of total`,
    },
    {
      label: 'Avg Risk Score',
      value: `${stats.average_risk_score}%`,
      icon: Activity,
      color: 'from-amber-500 to-orange-500',
      bgColor: 'bg-amber-50',
      textColor: 'text-amber-600',
      change: `Median: ${stats.median_risk_score}%`,
    },
    {
      label: 'Readmission Rate',
      value: `${stats.readmission_rate}%`,
      icon: TrendingUp,
      color: 'from-purple-500 to-purple-600',
      bgColor: 'bg-purple-50',
      textColor: 'text-purple-600',
      change: 'National avg: 18%',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="stat-card group"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {card.label}
                </p>
                <p className="mt-2 text-2xl font-bold text-gray-900 tracking-tight">
                  {card.value}
                </p>
                {card.change && (
                  <p className="mt-1 text-xs text-gray-400">{card.change}</p>
                )}
              </div>
              <div className={`w-10 h-10 rounded-lg ${card.bgColor} flex items-center justify-center`}>
                <Icon className={`w-5 h-5 ${card.textColor}`} />
              </div>
            </div>

            {/* Decorative bottom gradient */}
            <div className={`absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r ${card.color} opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-b-xl`} />
          </motion.div>
        );
      })}
    </div>
  );
}
