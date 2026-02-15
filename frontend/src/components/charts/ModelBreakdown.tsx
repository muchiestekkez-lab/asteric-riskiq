'use client';

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface ModelBreakdownProps {
  breakdown: Record<string, number>;
  confidence: number;
}

const MODEL_DISPLAY_NAMES: Record<string, string> = {
  xgboost: 'XGBoost',
  lightgbm: 'LightGBM',
  random_forest: 'Random Forest',
  gradient_boosting: 'Gradient Boost',
  neural_network: 'Neural Net',
};

export default function ModelBreakdown({ breakdown, confidence }: ModelBreakdownProps) {
  const data = Object.entries(breakdown).map(([model, score]) => ({
    model: MODEL_DISPLAY_NAMES[model] || model,
    score,
  })).sort((a, b) => b.score - a.score);

  const getColor = (score: number) => {
    if (score >= 75) return '#dc2626';
    if (score >= 55) return '#ef4444';
    if (score >= 30) return '#f59e0b';
    return '#10b981';
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-gray-900">Model Agreement</h4>
        <span className="text-xs text-gray-500">
          Confidence: <span className="font-semibold text-gray-900">{confidence}%</span>
        </span>
      </div>
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
              dataKey="model"
              type="category"
              tick={{ fontSize: 10, fill: '#64748b', fontWeight: 500 }}
              tickLine={false}
              axisLine={false}
              width={95}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              formatter={(value: number) => [`${value}%`, 'Prediction']}
            />
            <Bar dataKey="score" radius={[0, 6, 6, 0]} maxBarSize={20}>
              {data.map((entry, i) => (
                <Cell key={i} fill={getColor(entry.score)} fillOpacity={0.8} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
