import React from 'react';
import { useApp } from '../state/AppContext';
import { MetricType } from '../types/contract';
import { Moon, Sun, Sliders, Layers, RefreshCw } from 'lucide-react';
import { formatMetricName } from '../lib/colors';

export const Navbar: React.FC = () => {
  const {
    activeMetric,
    setActiveMetric,
    threshold,
    setThreshold,
    linkWeightMin,
    setLinkWeightMin,
    isDarkMode,
    toggleTheme,
    data,
    isLoading
  } = useApp();

  const metrics: { id: MetricType; label: string }[] = [
    { id: 'betweenness', label: 'Betweenness Centrality' },
    { id: 'degree', label: 'Degree Centrality' },
    { id: 'clustering', label: 'Clustering Coefficient' },
    { id: 'eigenvector', label: 'Eigenvector Centrality' },
    { id: 'landslide_density', label: 'Landslide Density (pts/km²)' },
    { id: 'mean_slope', label: 'Mean Slope (degrees)' },
    { id: 'extreme_days_aug2018', label: 'Aug 2018 Extreme Days' },
  ];

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 md:px-6 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <img
          src="/logo.png"
          alt="Vyuham Logo"
          className="w-10 h-10 object-contain rounded-full shadow-sm border border-emerald-500/30"
          onError={(e) => {
            // fallback if image is not loaded
            (e.target as HTMLElement).style.display = 'none';
          }}
        />
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold tracking-wider text-emerald-600 dark:text-emerald-400 text-lg">VYUHAM</span>
            <span className="hidden sm:inline-block text-xs uppercase px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 font-semibold">
              Kerala Climate Network
            </span>
          </div>
          <p className="hidden md:block text-[11px] text-slate-500 dark:text-slate-400">
            Complex System Science & Spatial Network Robustness
          </p>
        </div>
      </div>

      {/* Global Controls */}
      <div className="flex items-center gap-2 md:gap-4">
        {/* Metric Selector */}
        <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800/80 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
          <Layers className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400 hidden sm:inline" />
          <label className="text-xs font-medium text-slate-600 dark:text-slate-300 hidden lg:inline">Metric:</label>
          <select
            value={activeMetric}
            onChange={(e) => setActiveMetric(e.target.value as MetricType)}
            className="text-xs bg-transparent text-slate-800 dark:text-slate-100 font-medium focus:outline-none cursor-pointer"
          >
            {metrics.map((m) => (
              <option key={m.id} value={m.id} className="dark:bg-slate-900 text-slate-800 dark:text-slate-100">
                {m.label}
              </option>
            ))}
          </select>
        </div>

        {/* Threshold Selector (90 / 95 / 97) */}
        <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800/80 p-1 rounded-lg border border-slate-200 dark:border-slate-700">
          <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 px-1 hidden md:inline">Threshold:</span>
          {([90, 95, 97] as const).map((t) => (
            <button
              key={t}
              onClick={() => setThreshold(t)}
              className={`text-xs px-2 py-0.5 rounded font-medium transition-colors ${
                threshold === t
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
              }`}
            >
              p{t}
            </button>
          ))}
        </div>

        {/* Link Weight Slider */}
        <div className="hidden xl:flex items-center gap-2 bg-slate-100 dark:bg-slate-800/80 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
          <Sliders className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
          <span className="text-xs text-slate-600 dark:text-slate-300">Q Min:</span>
          <input
            type="range"
            min="0.30"
            max="0.80"
            step="0.01"
            value={linkWeightMin}
            onChange={(e) => setLinkWeightMin(parseFloat(e.target.value))}
            className="w-16 h-1.5 bg-slate-300 dark:bg-slate-600 rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />
          <span className="text-xs font-mono text-emerald-600 dark:text-emerald-400">{linkWeightMin.toFixed(2)}</span>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          aria-label="Toggle theme"
          className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors border border-slate-200 dark:border-slate-700"
        >
          {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />}
        </button>
      </div>
    </header>
  );
};
