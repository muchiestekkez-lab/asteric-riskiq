'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, Users, BarChart3, Bell, UserPlus,
  Upload, Activity, Shield, Brain, Zap, LogOut,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/auth-context';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Patients', href: '/patients', icon: Users },
  { name: 'Add Patient', href: '/data-entry', icon: UserPlus },
  { name: 'Import CSV', href: '/import', icon: Upload },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Alerts', href: '/alerts', icon: Bell },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { hospitalName, logout } = useAuth();

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-[260px] bg-surface-900 flex flex-col z-50">
      {/* Logo */}
      <div className="px-5 py-6 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight">
              Asteric <span className="text-brand-400">RiskIQ</span>
            </h1>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest font-medium">
              Readmission AI
            </p>
          </div>
        </div>
      </div>

      {/* Hospital Name */}
      {hospitalName && (
        <div className="px-5 py-3 border-b border-white/5">
          <p className="text-[10px] text-gray-500 uppercase tracking-widest font-medium mb-1">Hospital</p>
          <p className="text-sm text-gray-300 font-medium truncate">{hospitalName}</p>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <p className="px-3 py-2 text-[10px] uppercase tracking-widest text-gray-500 font-semibold">
          Main
        </p>
        {navigation.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href));
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                isActive ? 'sidebar-link-active' : 'sidebar-link-inactive'
              )}
            >
              <Icon className="w-[18px] h-[18px]" />
              <span>{item.name}</span>
              {item.name === 'Alerts' && (
                <span className="ml-auto w-5 h-5 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center">
                  !
                </span>
              )}
            </Link>
          );
        })}

        <div className="pt-4">
          <p className="px-3 py-2 text-[10px] uppercase tracking-widest text-gray-500 font-semibold">
            Intelligence
          </p>
          <div className="sidebar-link-inactive cursor-default opacity-70">
            <Shield className="w-[18px] h-[18px]" />
            <span>Model Health</span>
            <span className="ml-auto text-[10px] text-emerald-400 font-medium">STABLE</span>
          </div>
          <div className="sidebar-link-inactive cursor-default opacity-70">
            <Zap className="w-[18px] h-[18px]" />
            <span>Drift Monitor</span>
            <span className="ml-auto w-2 h-2 rounded-full bg-emerald-400"></span>
          </div>
        </div>
      </nav>

      {/* Bottom section */}
      <div className="px-3 py-4 border-t border-white/5">
        <div className="px-3 py-3 rounded-lg bg-white/5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-400 to-purple-500 flex items-center justify-center">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-300">AI Engine</p>
              <p className="text-[10px] text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block"></span>
                5 Models Active
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={logout}
          className="mt-3 w-full flex items-center gap-2 px-3 py-2 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors text-sm"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>

        <p className="mt-2 px-3 text-[10px] text-gray-600 text-center">
          v1.0.0 &middot; Partner Access
        </p>
      </div>
    </aside>
  );
}
