'use client';

import { motion } from 'framer-motion';
import { ArrowUp, ArrowDown, Lightbulb } from 'lucide-react';
import type { RiskFactor, Counterfactual } from '@/types';
import { cn } from '@/lib/utils';

interface RiskFactorsProps {
  factors: RiskFactor[];
  naturalLanguage: string;
  counterfactuals: Counterfactual[];
}

export default function RiskFactors({ factors, naturalLanguage, counterfactuals }: RiskFactorsProps) {
  const increasing = factors.filter(f => f.impact === 'increases');
  const decreasing = factors.filter(f => f.impact === 'decreases');
  const maxAbsImpact = Math.max(...factors.map(f => f.abs_impact), 0.001);

  return (
    <div className="space-y-5">
      {/* Natural Language Explanation */}
      <div className="p-4 rounded-lg bg-blue-50 border border-blue-100">
        <p className="text-sm text-blue-800 leading-relaxed">{naturalLanguage}</p>
      </div>

      {/* SHAP Factor Visualization */}
      <div>
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Risk Factor Impact (SHAP Analysis)</h4>
        <div className="space-y-2">
          {factors.slice(0, 12).map((factor, idx) => (
            <motion.div
              key={factor.feature}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.03 }}
              className="flex items-center gap-3 group"
            >
              {/* Factor name */}
              <div className="w-44 flex-shrink-0">
                <p className="text-xs font-medium text-gray-600 truncate" title={factor.display_name}>
                  {factor.display_name}
                </p>
              </div>

              {/* Impact bar */}
              <div className="flex-1 flex items-center">
                <div className="relative w-full h-5 flex items-center">
                  {/* Center line */}
                  <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-200" />

                  {/* Bar */}
                  <div
                    className={cn('absolute h-4 rounded transition-all duration-500', {
                      'bg-red-400/80': factor.impact === 'increases',
                      'bg-emerald-400/80': factor.impact === 'decreases',
                    })}
                    style={{
                      width: `${(factor.abs_impact / maxAbsImpact) * 45}%`,
                      left: factor.impact === 'increases' ? '50%' : undefined,
                      right: factor.impact === 'decreases' ? '50%' : undefined,
                    }}
                  />
                </div>
              </div>

              {/* Value & direction */}
              <div className="w-24 flex-shrink-0 flex items-center gap-1 justify-end">
                {factor.impact === 'increases' ? (
                  <ArrowUp className="w-3 h-3 text-red-500" />
                ) : (
                  <ArrowDown className="w-3 h-3 text-emerald-500" />
                )}
                <span className={cn('text-xs font-mono font-medium', {
                  'text-red-600': factor.impact === 'increases',
                  'text-emerald-600': factor.impact === 'decreases',
                })}>
                  {factor.shap_value > 0 ? '+' : ''}{factor.shap_value.toFixed(3)}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Counterfactual Insights */}
      {counterfactuals.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="w-4 h-4 text-amber-500" />
            <h4 className="text-sm font-semibold text-gray-900">What Could Reduce Risk</h4>
          </div>
          <div className="space-y-2">
            {counterfactuals.map((cf, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + idx * 0.05 }}
                className="p-3 rounded-lg border border-amber-100 bg-amber-50/50"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-xs font-semibold text-gray-800">{cf.factor}</p>
                    <p className="text-[11px] text-gray-500 mt-0.5">
                      {cf.current} &rarr; {cf.target}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">{cf.action}</p>
                  </div>
                  <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
                    -{cf.estimated_risk_reduction}%
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
