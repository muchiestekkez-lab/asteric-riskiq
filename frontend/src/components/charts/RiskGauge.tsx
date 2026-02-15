'use client';

import { useEffect, useState } from 'react';
import type { RiskLevel } from '@/types';
import { getRiskColor } from '@/lib/utils';

interface RiskGaugeProps {
  score: number;
  level: RiskLevel;
  size?: number;
  showLabel?: boolean;
}

export default function RiskGauge({ score, level, size = 180, showLabel = true }: RiskGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setAnimatedScore(score), 100);
    return () => clearTimeout(timer);
  }, [score]);

  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * Math.PI; // Half circle
  const center = size / 2;
  const dashOffset = circumference - (animatedScore / 100) * circumference;
  const color = getRiskColor(level);

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size / 2 + 30} viewBox={`0 0 ${size} ${size / 2 + 30}`}>
        {/* Background arc */}
        <path
          d={`M ${strokeWidth / 2} ${center} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${center}`}
          fill="none"
          stroke="#f1f5f9"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Colored arc */}
        <path
          d={`M ${strokeWidth / 2} ${center} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${center}`}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          className="gauge-ring"
          style={{ filter: `drop-shadow(0 0 6px ${color}40)` }}
        />

        {/* Score text */}
        <text
          x={center}
          y={center - 8}
          textAnchor="middle"
          className="text-3xl font-bold"
          fill={color}
          style={{ fontSize: size * 0.2 }}
        >
          {Math.round(animatedScore)}%
        </text>

        {showLabel && (
          <text
            x={center}
            y={center + 16}
            textAnchor="middle"
            fill="#94a3b8"
            style={{ fontSize: 11, fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}
          >
            {level} risk
          </text>
        )}
      </svg>
    </div>
  );
}
