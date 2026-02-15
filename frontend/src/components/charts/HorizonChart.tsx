'use client';

import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts';
import type { RiskHorizons } from '@/types';

interface HorizonChartProps {
  horizons: RiskHorizons;
}

export default function HorizonChart({ horizons }: HorizonChartProps) {
  const data = [
    { label: '24 Hours', value: horizons['24h'], key: '24h' },
    { label: '72 Hours', value: horizons['72h'], key: '72h' },
    { label: '7 Days', value: horizons['7d'], key: '7d' },
    { label: '30 Days', value: horizons['30d'], key: '30d' },
  ];

  const getColor = (value: number) => {
    if (value >= 75) return '#dc2626';
    if (value >= 55) return '#ef4444';
    if (value >= 30) return '#f59e0b';
    return '#10b981';
  };

  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-900 mb-3">Multi-Horizon Prediction</h4>
      <div className="h-44">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 10, bottom: 0, left: 0 }}>
            <XAxis
              type="number"
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${v}%`}
            />
            <YAxis
              dataKey="label"
              type="category"
              tick={{ fontSize: 11, fill: '#64748b', fontWeight: 500 }}
              tickLine={false}
              axisLine={false}
              width={70}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              formatter={(value: number) => [`${value}%`, 'Risk']}
            />
            <Bar dataKey="value" radius={[0, 6, 6, 0]} maxBarSize={24}>
              {data.map((entry, i) => (
                <Cell key={i} fill={getColor(entry.value)} fillOpacity={0.85} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
