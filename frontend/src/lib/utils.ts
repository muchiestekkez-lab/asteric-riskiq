// Asteric RiskIQ - Utility Functions

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { RiskLevel } from '@/types';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getRiskColor(level: RiskLevel): string {
  const colors: Record<RiskLevel, string> = {
    low: '#10b981',
    medium: '#f59e0b',
    high: '#ef4444',
    critical: '#dc2626',
  };
  return colors[level] || '#6b7280';
}

export function getRiskBgClass(level: RiskLevel): string {
  const classes: Record<RiskLevel, string> = {
    low: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    medium: 'bg-amber-50 text-amber-700 border-amber-200',
    high: 'bg-red-50 text-red-700 border-red-200',
    critical: 'bg-red-100 text-red-800 border-red-300',
  };
  return classes[level] || 'bg-gray-50 text-gray-700';
}

export function getRiskDotClass(level: RiskLevel): string {
  const classes: Record<RiskLevel, string> = {
    low: 'bg-emerald-500',
    medium: 'bg-amber-500',
    high: 'bg-red-500',
    critical: 'bg-red-600 animate-pulse',
  };
  return classes[level] || 'bg-gray-500';
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return '-';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

export function formatDateTime(dateStr: string): string {
  if (!dateStr) return '-';
  try {
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

export function formatScore(score: number): string {
  return `${Math.round(score)}%`;
}

export function getUrgencyColor(urgency: string): string {
  const colors: Record<string, string> = {
    immediate: 'text-red-600 bg-red-50 border-red-200',
    before_discharge: 'text-amber-600 bg-amber-50 border-amber-200',
    post_discharge: 'text-blue-600 bg-blue-50 border-blue-200',
  };
  return colors[urgency] || 'text-gray-600 bg-gray-50';
}

export function getEvidenceBadge(level: string): string {
  const badges: Record<string, string> = {
    A: 'bg-emerald-100 text-emerald-800',
    B: 'bg-blue-100 text-blue-800',
    C: 'bg-gray-100 text-gray-800',
  };
  return badges[level] || 'bg-gray-100 text-gray-800';
}

export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen) + '...';
}
