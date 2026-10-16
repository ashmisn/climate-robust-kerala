import React from 'react';
import { useApp, PageId } from '../state/AppContext';
import {
  LayoutDashboard,
  Share2,
  ShieldAlert,
  Waves,
  Mountain,
  BookOpen,
  ChevronRight
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { activePage, setActivePage } = useApp();

  const navItems: { id: PageId; label: string; badge?: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'network', label: 'Network Explorer', icon: Share2 },
    { id: 'robustness', label: 'Robustness (Study A)', badge: 'Study A', icon: ShieldAlert },
    { id: 'basins', label: 'Basins Impact', icon: Waves },
    { id: 'landslide', label: 'Landslide Validation', badge: 'Study B', icon: Mountain },
    { id: 'method', label: 'Method & Limits', icon: BookOpen },
  ];

  return (
    <aside className="w-full md:w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between shrink-0 transition-colors">
      <div className="p-3 md:p-4 space-y-1">
        <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
          Navigation
        </div>
        <nav className="flex md:flex-col gap-1 overflow-x-auto md:overflow-visible pb-1 md:pb-0">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActivePage(item.id)}
                className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-xs md:text-sm font-medium transition-all whitespace-nowrap md:whitespace-normal w-full ${
                  isActive
                    ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-semibold shadow-xs border border-emerald-500/20'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400 dark:text-slate-500'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded font-bold hidden lg:inline-block ${
                    isActive
                      ? 'bg-emerald-200/60 dark:bg-emerald-800/60 text-emerald-900 dark:text-emerald-200'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Info in Sidebar */}
      <div className="hidden md:block p-4 border-t border-slate-200 dark:border-slate-800 text-[11px] text-slate-400 dark:text-slate-500 space-y-1">
        <div className="font-medium text-slate-600 dark:text-slate-300">Kerala Monsoon 1991–2020</div>
        <div>IMD 0.25° • India-WRIS • SRTM</div>
        <div className="pt-2 text-[10px] text-emerald-600 dark:text-emerald-400 font-mono">
          Reproducible Pipeline v1.0
        </div>
      </div>
    </aside>
  );
};
