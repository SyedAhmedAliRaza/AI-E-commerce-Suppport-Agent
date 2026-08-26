'use client';

import React from 'react';
import { SystemHealth } from '@/types';
import { Bot } from 'lucide-react';

interface HeaderProps {
  health?: SystemHealth | null;
}

export const Header: React.FC<HeaderProps> = ({ health }) => {
  return (
    <header className="sticky top-0 z-40 glass-panel border-b border-slate-800/80 px-4 lg:px-8 py-3.5 mb-6">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative p-2.5 rounded-xl bg-gradient-to-tr from-cyan-600 to-teal-500 text-white shadow-lg shadow-cyan-500/20">
            <Bot className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-cyan-300 bg-clip-text text-transparent">
              TechMania AI Support
            </h1>
            <p className="text-xs text-slate-400">E-Commerce Customer Support & Automated Refund Portal</p>
          </div>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs text-slate-300">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-medium text-emerald-300">System Online</span>
        </div>
      </div>
    </header>
  );
};
