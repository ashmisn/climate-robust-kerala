import React, { useState } from 'react';
import { useApp } from '../state/AppContext';
import { MapView } from '../components/MapView';
import { formatMetricName } from '../lib/colors';
import { Sliders, Activity, Info, ListFilter } from 'lucide-react';

export const NetworkExplorer: React.FC = () => {
  const {
    data,
    activeMetric,
    linkWeightMin,
    setLinkWeightMin,
    selectedCell,
    setSelectedCell
  } = useApp();

  const [filterBasin, setFilterBasin] = useState<string>('all');

  if (!data) return null;

  // Filter links based on current cutoff
  const activeLinks = data.links.filter((l) => l.weight >= linkWeightMin);

  // Basins list for filter
  const basinsList = Array.from(new Set(data.cells.features.map((f) => f.properties.basin_name || f.properties.basin_id)));

  // Ranked cells by active metric
  const rankedCells = [...data.cells.features]
    .map((f) => f.properties)
    .filter((c) => filterBasin === 'all' || (c.basin_name || c.basin_id) === filterBasin)
    .sort((a, b) => ((b as any)[activeMetric] || 0) - ((a as any)[activeMetric] || 0));

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header & Controls Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Activity className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            Network Explorer
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Analyze synchronization links (Q ≥ {linkWeightMin.toFixed(2)}) across the 0.25° grid network.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Basin Filter */}
          <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-xs">
            <ListFilter className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-500 hidden sm:inline">Basin:</span>
            <select
              value={filterBasin}
              onChange={(e) => setFilterBasin(e.target.value)}
              className="bg-transparent text-slate-800 dark:text-slate-200 font-medium focus:outline-none cursor-pointer"
            >
              <option value="all" className="dark:bg-slate-900">All Regions</option>
              {basinsList.map((b) => (
                <option key={b} value={b} className="dark:bg-slate-900">{b}</option>
              ))}
            </select>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-3 text-xs bg-slate-50 dark:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
            <div>
              <span className="text-slate-400">Active Edges: </span>
              <strong className="text-emerald-600 dark:text-emerald-400 font-mono">{activeLinks.length}</strong>
              <span className="text-slate-400"> / {data.links.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Map & Cell Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map Panel (2 Cols) */}
        <div className="lg:col-span-2 space-y-2">
          <MapView heightClass="h-[600px]" showLinksDefault={true} />
          <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
            <span>Tip: Click on any cell polygon to open detailed properties in the right inspector drawer.</span>
            <span>Esri & Open GIS Basemaps • Leaflet</span>
          </div>
        </div>

        {/* Ranked Nodes Panel (1 Col) */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-xs flex flex-col h-[600px]">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2 mb-2">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-200">
                Cell Leaderboard
              </h2>
              <p className="text-[11px] text-slate-400">Sorted by {formatMetricName(activeMetric)}</p>
            </div>
            <span className="text-xs font-mono bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 px-2 py-0.5 rounded font-semibold">
              {rankedCells.length} cells
            </span>
          </div>

          <div className="overflow-y-auto flex-1 space-y-1.5 pr-1">
            {rankedCells.map((cell, idx) => {
              const isSelected = selectedCell?.cell_id === cell.cell_id;
              const val = (cell as any)[activeMetric];
              return (
                <div
                  key={cell.cell_id}
                  onClick={() => setSelectedCell(cell)}
                  className={`p-2.5 rounded-lg text-xs cursor-pointer transition-all border ${
                    isSelected
                      ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500/40 text-emerald-900 dark:text-emerald-200 shadow-xs'
                      : 'bg-slate-50/50 dark:bg-slate-800/30 border-slate-200/60 dark:border-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-slate-400 font-medium text-[11px]">#{idx + 1}</span>
                      <strong className="font-mono">{cell.cell_id}</strong>
                    </div>
                    <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                      {typeof val === 'number' ? val.toFixed(4) : val}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                    <span className="truncate max-w-[140px]">{cell.basin_name || cell.basin_id}</span>
                    <span>{cell.lat.toFixed(2)}°N, {cell.lon.toFixed(2)}°E</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
