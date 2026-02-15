'use client';

import { motion } from 'framer-motion';
import {
  Clock, Phone, Home, Video, Pill, UserCheck,
  BookOpen, HeartHandshake, Calendar, Wifi,
  AlertCircle, CheckCircle,
} from 'lucide-react';
import type { Intervention } from '@/types';
import { cn, getUrgencyColor, getEvidenceBadge } from '@/lib/utils';

interface InterventionPanelProps {
  interventions: Intervention[];
  riskScore: number;
}

const INTERVENTION_ICONS: Record<string, any> = {
  delay_discharge: Clock,
  nurse_followup: HeartHandshake,
  phone_followup_24h: Phone,
  phone_followup_72h: Phone,
  home_visit: Home,
  telehealth: Video,
  medication_reconciliation: Pill,
  care_coordinator: UserCheck,
  patient_education: BookOpen,
  social_work_consult: HeartHandshake,
  rapid_clinic_appointment: Calendar,
  remote_monitoring: Wifi,
};

const URGENCY_LABELS: Record<string, string> = {
  immediate: 'Immediate',
  before_discharge: 'Before Discharge',
  post_discharge: 'Post Discharge',
};

export default function InterventionPanel({ interventions, riskScore }: InterventionPanelProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-semibold text-gray-900">Recommended Interventions</h4>
        <span className="text-xs text-gray-500">{interventions.length} actions</span>
      </div>

      <div className="space-y-3">
        {interventions.map((intervention, idx) => {
          const Icon = INTERVENTION_ICONS[intervention.id] || AlertCircle;

          return (
            <motion.div
              key={`${intervention.id}-${idx}`}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="p-3.5 rounded-lg border border-gray-100 hover:border-gray-200 transition-all group"
            >
              <div className="flex items-start gap-3">
                <div className={cn(
                  'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
                  intervention.urgency === 'immediate'
                    ? 'bg-red-100 text-red-600'
                    : intervention.urgency === 'before_discharge'
                      ? 'bg-amber-100 text-amber-600'
                      : 'bg-blue-100 text-blue-600'
                )}>
                  <Icon className="w-4 h-4" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-gray-900">{intervention.name}</p>
                    <span className={cn(
                      'text-[10px] font-medium px-1.5 py-0.5 rounded border',
                      getUrgencyColor(intervention.urgency)
                    )}>
                      {URGENCY_LABELS[intervention.urgency] || intervention.urgency}
                    </span>
                  </div>

                  <p className="text-xs text-gray-500 mt-1">{intervention.description}</p>
                  <p className="text-xs text-gray-400 mt-1 italic">{intervention.rationale}</p>

                  <div className="flex items-center gap-3 mt-2">
                    <span className={cn(
                      'text-[10px] font-semibold px-1.5 py-0.5 rounded',
                      getEvidenceBadge(intervention.evidence_level)
                    )}>
                      Evidence: {intervention.evidence_level}
                    </span>
                    <span className="text-[10px] text-gray-400">
                      Cost: {intervention.cost_category}
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
