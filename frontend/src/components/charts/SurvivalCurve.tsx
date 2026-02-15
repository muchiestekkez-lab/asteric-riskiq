'use client';

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import type { SurvivalData } from '@/types';

interface SurvivalCurveProps {
  data: SurvivalData | null;
}

export default function SurvivalCurve({ data }: SurvivalCurveProps) {
  if (!data) {
    return <div className="h-64 skeleton rounded-lg" />;
  }

  const chartData = data.curve.map((point) => ({
    day: point.day,
    probability: Math.round(point.survival_probability * 100),
    at_risk: point.at_risk,
  }));

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-sm font-semibold text-gray-900">Survival Curve (Kaplan-Meier)</h4>
          <p className="text-xs text-gray-400 mt-0.5">
            Probability of remaining out of hospital over time
          </p>
        </div>
        <div className="text-right">
          {data.median_survival_days && (
            <p className="text-xs text-gray-500">
              Median: <span className="font-semibold text-gray-900">{data.median_survival_days} days</span>
            </p>
          )}
          <p className="text-xs text-gray-400">
            Event rate: {(data.event_rate * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
            <defs>
              <linearGradient id="survivalGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="day"
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
              label={{ value: 'Days Post-Discharge', position: 'insideBottom', offset: -2, fontSize: 10, fill: '#94a3b8' }}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              tickLine={false}
              axisLine={false}
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                fontSize: '12px',
                boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
              }}
              formatter={(value: number) => [`${value}%`, 'Survival Probability']}
              labelFormatter={(day) => `Day ${day}`}
            />
            <ReferenceLine y={50} stroke="#ef4444" strokeDasharray="5 5" strokeOpacity={0.5} />
            <Area
              type="stepAfter"
              dataKey="probability"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#survivalGradient)"
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
