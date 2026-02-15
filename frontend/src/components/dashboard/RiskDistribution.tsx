'use client';

import { motion } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie,
} from 'recharts';
import type { DashboardStats, RiskDistributionBin } from '@/types';

interface RiskDistributionProps {
  stats: DashboardStats | null;
  distribution: RiskDistributionBin[];
}

export default function RiskDistribution({ stats, distribution }: RiskDistributionProps) {
  if (!stats) return null;

  const pieData = [
    { name: 'Critical', value: stats.risk_distribution.critical, color: '#dc2626' },
    { name: 'High', value: stats.risk_distribution.high, color: '#ef4444' },
    { name: 'Medium', value: stats.risk_distribution.medium, color: '#f59e0b' },
    { name: 'Low', value: stats.risk_distribution.low, color: '#10b981' },
  ].filter(d => d.value > 0);

  const getBarColor = (min: number) => {
    if (min >= 75) return '#dc2626';
    if (min >= 55) return '#ef4444';
    if (min >= 30) return '#f59e0b';
    return '#10b981';
  };

  const wardData = Object.entries(stats.ward_breakdown).map(([name, data]) => ({
    name,
    count: data.count,
    avg_risk: data.avg_risk,
    high_risk: data.high_risk_count,
  })).sort((a, b) => b.avg_risk - a.avg_risk);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Risk Distribution Histogram */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card p-5 lg:col-span-2"
      >
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Risk Score Distribution</h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={distribution} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                dataKey="range"
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                tickLine={false}
                axisLine={{ stroke: '#e2e8f0' }}
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  fontSize: '12px',
                  boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={30}>
                {distribution.map((entry, i) => (
                  <Cell key={i} fill={getBarColor(entry.min)} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Risk Level Breakdown */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card p-5"
      >
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Risk Levels</h3>
        <div className="h-40 mb-4">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={65}
                paddingAngle={3}
                dataKey="value"
              >
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="space-y-2">
          {pieData.map((item) => (
            <div key={item.name} className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-gray-600 font-medium">{item.name}</span>
              </div>
              <span className="font-semibold text-gray-900">{item.value}</span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Ward Breakdown */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card p-5 lg:col-span-3"
      >
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Risk by Ward</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
          {wardData.map((ward) => (
            <div
              key={ward.name}
              className="p-3 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors"
            >
              <p className="text-[11px] text-gray-500 font-medium truncate">{ward.name}</p>
              <p className="text-lg font-bold text-gray-900 mt-1">{ward.avg_risk}%</p>
              <div className="flex items-center justify-between mt-1">
                <span className="text-[10px] text-gray-400">{ward.count} pts</span>
                {ward.high_risk > 0 && (
                  <span className="text-[10px] text-red-500 font-medium">
                    {ward.high_risk} high
                  </span>
                )}
              </div>
              {/* Mini bar */}
              <div className="mt-2 h-1 bg-gray-100 rounded-full">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${Math.min(ward.avg_risk, 100)}%`,
                    backgroundColor: ward.avg_risk >= 70 ? '#ef4444' :
                      ward.avg_risk >= 50 ? '#f59e0b' : '#10b981',
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
