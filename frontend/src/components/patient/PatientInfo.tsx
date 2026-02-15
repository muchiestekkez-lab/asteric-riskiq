'use client';

import {
  User, Calendar, Stethoscope, Pill, Heart,
  Thermometer, Droplets, Activity, Wind,
  Home, Car, Users, Building,
} from 'lucide-react';
import type { PatientInfo as PatientInfoType } from '@/types';
import { formatDate, cn } from '@/lib/utils';

interface PatientInfoProps {
  info: PatientInfoType;
}

export default function PatientInfoCard({ info }: PatientInfoProps) {
  return (
    <div className="space-y-5">
      {/* Demographics */}
      <div>
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Demographics</h4>
        <div className="grid grid-cols-2 gap-3">
          <InfoItem icon={User} label="Age / Gender" value={`${info.age}y ${info.gender}`} />
          <InfoItem icon={Building} label="Ward" value={info.ward} />
          <InfoItem icon={Calendar} label="Admitted" value={formatDate(info.admission_date)} />
          <InfoItem icon={Calendar} label="Discharged" value={formatDate(info.discharge_date)} />
          <InfoItem icon={Stethoscope} label="Diagnosis" value={`${info.diagnosis} (${info.diagnosis_code})`} />
          <InfoItem icon={Pill} label="Medications" value={`${info.medication_count} active`} />
        </div>
      </div>

      {/* Chronic Conditions */}
      {info.chronic_conditions.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Chronic Conditions
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {info.chronic_conditions.map((condition) => (
              <span
                key={condition}
                className="px-2 py-1 text-[11px] font-medium bg-purple-50 text-purple-700 rounded-md border border-purple-100"
              >
                {condition}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Vital Signs */}
      <div>
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Vital Signs</h4>
        <div className="grid grid-cols-3 gap-2">
          <VitalItem
            label="BP"
            value={`${info.vitals.bp_systolic}/${info.vitals.bp_diastolic}`}
            unit="mmHg"
            alert={info.vitals.bp_systolic > 160 || info.vitals.bp_systolic < 90}
          />
          <VitalItem
            label="HR"
            value={`${info.vitals.heart_rate}`}
            unit="bpm"
            alert={info.vitals.heart_rate > 100 || info.vitals.heart_rate < 50}
          />
          <VitalItem
            label="Temp"
            value={`${info.vitals.temperature}`}
            unit="F"
            alert={info.vitals.temperature > 100.4}
          />
          <VitalItem
            label="SpO2"
            value={`${info.vitals.oxygen_saturation}`}
            unit="%"
            alert={info.vitals.oxygen_saturation < 92}
          />
          <VitalItem
            label="RR"
            value={`${info.vitals.respiratory_rate}`}
            unit="/min"
            alert={info.vitals.respiratory_rate > 24}
          />
          <VitalItem
            label="BMI"
            value={`${info.bmi}`}
            unit=""
            alert={info.bmi > 35 || info.bmi < 18}
          />
        </div>
      </div>

      {/* Labs */}
      <div>
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Lab Results</h4>
        <div className="grid grid-cols-2 gap-2">
          <LabItem label="Hemoglobin" value={info.labs.hemoglobin} unit="g/dL" alert={info.labs.hemoglobin < 10} />
          <LabItem label="WBC" value={info.labs.wbc_count} unit="K/uL" alert={info.labs.wbc_count > 12} />
          <LabItem label="Creatinine" value={info.labs.creatinine} unit="mg/dL" alert={info.labs.creatinine > 1.5} />
          <LabItem label="Glucose" value={info.labs.glucose} unit="mg/dL" alert={info.labs.glucose > 200} />
          <LabItem label="BUN" value={info.labs.bun} unit="mg/dL" alert={info.labs.bun > 25} />
          <LabItem label="Na+" value={info.labs.sodium} unit="mEq/L" alert={info.labs.sodium < 135} />
          <LabItem label="K+" value={info.labs.potassium} unit="mEq/L" alert={info.labs.potassium > 5.0} />
        </div>
      </div>

      {/* Social Factors */}
      <div>
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Social Factors</h4>
        <div className="grid grid-cols-2 gap-2">
          <SocialItem
            icon={Home}
            label="Lives Alone"
            value={info.social_factors.lives_alone}
            risk={info.social_factors.lives_alone}
          />
          <SocialItem
            icon={Users}
            label="Has Caregiver"
            value={info.social_factors.has_caregiver}
            risk={!info.social_factors.has_caregiver}
          />
          <SocialItem
            icon={Car}
            label="Transportation"
            value={info.social_factors.transportation_access}
            risk={!info.social_factors.transportation_access}
          />
          <SocialItem
            icon={Building}
            label="Stable Housing"
            value={info.social_factors.housing_stable}
            risk={!info.social_factors.housing_stable}
          />
        </div>
      </div>
    </div>
  );
}

function InfoItem({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-gray-50">
      <Icon className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
      <div className="min-w-0">
        <p className="text-[10px] text-gray-400">{label}</p>
        <p className="text-xs font-medium text-gray-700 truncate">{value}</p>
      </div>
    </div>
  );
}

function VitalItem({ label, value, unit, alert }: { label: string; value: string; unit: string; alert: boolean }) {
  return (
    <div className={cn(
      'p-2 rounded-lg text-center border',
      alert ? 'bg-red-50 border-red-100' : 'bg-gray-50 border-transparent'
    )}>
      <p className="text-[10px] text-gray-400">{label}</p>
      <p className={cn('text-sm font-bold', alert ? 'text-red-600' : 'text-gray-900')}>
        {value}
      </p>
      <p className="text-[9px] text-gray-400">{unit}</p>
    </div>
  );
}

function LabItem({ label, value, unit, alert }: { label: string; value: number; unit: string; alert: boolean }) {
  return (
    <div className={cn(
      'flex items-center justify-between p-2 rounded-lg',
      alert ? 'bg-red-50' : 'bg-gray-50'
    )}>
      <span className="text-[11px] text-gray-500">{label}</span>
      <span className={cn('text-xs font-semibold', alert ? 'text-red-600' : 'text-gray-900')}>
        {value} <span className="text-[9px] text-gray-400 font-normal">{unit}</span>
      </span>
    </div>
  );
}

function SocialItem({ icon: Icon, label, value, risk }: { icon: any; label: string; value: boolean; risk: boolean }) {
  return (
    <div className={cn(
      'flex items-center gap-2 p-2 rounded-lg',
      risk ? 'bg-amber-50' : 'bg-gray-50'
    )}>
      <Icon className={cn('w-3.5 h-3.5', risk ? 'text-amber-500' : 'text-gray-400')} />
      <div>
        <p className="text-[10px] text-gray-400">{label}</p>
        <p className={cn('text-xs font-medium', risk ? 'text-amber-700' : 'text-emerald-600')}>
          {value ? 'Yes' : 'No'}
        </p>
      </div>
    </div>
  );
}
