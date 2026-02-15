'use client';

import { useState } from 'react';
import { Search, RefreshCw } from 'lucide-react';

interface HeaderProps {
  title: string;
  subtitle?: string;
  onSearch?: (query: string) => void;
  onRefresh?: () => void;
  actions?: React.ReactNode;
}

export default function Header({ title, subtitle, onSearch, onRefresh, actions }: HeaderProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch?.(searchQuery);
  };

  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-lg border-b border-gray-100">
      <div className="px-6 py-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 tracking-tight">{title}</h2>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>
          )}
        </div>

        <div className="flex items-center gap-3">
          {onSearch && (
            <form onSubmit={handleSearch} className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search patients..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  onSearch?.(e.target.value);
                }}
                className="input-field pl-9 w-64"
              />
            </form>
          )}

          {onRefresh && (
            <button
              onClick={onRefresh}
              className="btn-secondary p-2"
              title="Refresh data"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}

          {actions}
        </div>
      </div>
    </header>
  );
}
