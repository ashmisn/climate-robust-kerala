import React from 'react';
import { useApp } from '../state/AppContext';
import { X, MapPin, Activity, Mountain, AlertCircle, Droplet, Hash } from 'lucide-react';

export const DetailDrawer: React.FC = () => {
  const {
    selectedCell,
    setSelectedCell,
    selectedBasin,
    setSelectedBasin,
    data
  } = useApp();

  if (!selectedCell && !selectedBasin) return null;

  const handleClose = () => {
    setSelectedCell(null);
    setSelectedBasin(null);
  };

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-full sm:w-96 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md shadow-2xl border-l border-slate-200 dark:border-slate-800 p-5 overflow-y-auto transition-transform">
      <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          {selectedCell ? (
            <>
              <MapPin className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">Cell Inspector</h3>
                <span className="text-xs font-mono text-slate-500 dark:text-slate-400">{selectedCell.cell_id}</span>
              </div>
            </>
          ) : (
            <>
              <Droplet className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">{selectedBasin?.name} Basin</h3>
                <span className="text-xs font-mono text-slate-500 dark:text-slate-400">Impact Rank #{selectedBasin?.impact_rank}</span>
              </div>
            </>
          )}
        </div>
        <button
          onClick={handleClose}
          className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {selectedCell && (
        <div className="mt-4 space-y-4 text-xs">
          {/* Spatial Info */}
          <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-700/60">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <span className="text-slate-400">Latitude</span>
                <p className="font-mono font-medium text-slate-800 dark:text-slate-200">{selectedCell.lat.toFixed(2)}°N</p>
              </div>
              <div>
                <span className="text-slate-400">Longitude</span>
                <p className="font-mono font-medium text-slate-800 dark:text-slate-200">{selectedCell.lon.toFixed(2)}°E</p>
              </div>
              <div className="col-span-2 pt-1 border-t border-slate-200/60 dark:border-slate-700/40">
                <span className="text-slate-400">Assigned Basin</span>
                <p className="font-medium text-emerald-600 dark:text-emerald-400">{selectedCell.basin_name || selectedCell.basin_id}</p>
              </div>
            </div>
          </div>

          {/* Network Centralities */}
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5" /> Network Centrality
            </h4>
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-500/20">
                <span className="text-slate-500 dark:text-slate-400">Betweenness</span>
                <p className="text-base font-bold font-mono text-emerald-700 dark:text-emerald-300">
                  {selectedCell.betweenness.toFixed(4)}
                </p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60">
                <span className="text-slate-500 dark:text-slate-400">Degree</span>
                <p className="text-base font-bold font-mono text-slate-800 dark:text-slate-200">
                  {selectedCell.degree.toFixed(4)}
                </p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60">
                <span className="text-slate-500 dark:text-slate-400">Clustering</span>
                <p className="text-base font-bold font-mono text-slate-800 dark:text-slate-200">
                  {selectedCell.clustering.toFixed(4)}
                </p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60">
                <span className="text-slate-500 dark:text-slate-400">Eigenvector</span>
                <p className="text-base font-bold font-mono text-slate-800 dark:text-slate-200">
                  {selectedCell.eigenvector.toFixed(4)}
                </p>
              </div>
            </div>
          </div>

          {/* Topography & DEM */}
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
              <Mountain className="w-3.5 h-3.5" /> Topography & DEM
            </h4>
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60">
                <span className="text-slate-500 dark:text-slate-400">Mean Slope</span>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{selectedCell.mean_slope.toFixed(1)}°</p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60">
                <span className="text-slate-500 dark:text-slate-400">Max Slope</span>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{selectedCell.max_slope.toFixed(1)}°</p>
              </div>
            </div>
          </div>

          {/* Landslide & Extreme Disasters */}
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5" /> 2018 Disasters
            </h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-red-50/60 dark:bg-red-950/20 border border-red-500/20">
                <div>
                  <span className="text-red-900 dark:text-red-300 font-medium">2018 Landslides Mapped</span>
                  <p className="text-[11px] text-red-600 dark:text-red-400">Density per km²</p>
                </div>
                <div className="text-right">
                  <div className="font-bold text-red-900 dark:text-red-200">{selectedCell.landslide_count_2018} pts</div>
                  <div className="text-[11px] font-mono text-red-700 dark:text-red-400">{selectedCell.landslide_density.toFixed(4)}</div>
                </div>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-blue-50/60 dark:bg-blue-950/20 border border-blue-500/20">
                <div>
                  <span className="text-blue-900 dark:text-blue-300 font-medium">August 2018 Extreme Days</span>
                  <p className="text-[11px] text-blue-600 dark:text-blue-400">Days above 95th pct</p>
                </div>
                <div className="font-bold text-blue-900 dark:text-blue-200 text-sm">
                  {selectedCell.extreme_days_aug2018} days
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedBasin && (
        <div className="mt-4 space-y-4 text-xs">
          <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-lg border border-slate-200 dark:border-slate-700/60 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Basin Impact Ranking</span>
              <span className="font-bold text-emerald-600 dark:text-emerald-400 text-sm">#{selectedBasin.impact_rank}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Total 0.25° Grid Cells</span>
              <span className="font-medium text-slate-800 dark:text-slate-200">{selectedBasin.n_cells} cells</span>
            </div>
          </div>

          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Disconnection Impact (Study A)
            </h4>
            <div className="space-y-2">
              <div className="p-3 rounded-lg bg-amber-50/60 dark:bg-amber-950/20 border border-amber-500/20">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-amber-900 dark:text-amber-300">LCC Drop if Basin Removed</span>
                  <span className="font-bold text-amber-900 dark:text-amber-200 text-sm">
                    {(selectedBasin.lcc_drop_if_removed * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-amber-200/50 dark:bg-amber-900/50 h-1.5 rounded-full mt-2 overflow-hidden">
                  <div
                    className="bg-amber-500 h-full rounded-full"
                    style={{ width: `${Math.min(100, selectedBasin.lcc_drop_if_removed * 100)}%` }}
                  />
                </div>
              </div>

              <div className="p-3 rounded-lg bg-rose-50/60 dark:bg-rose-950/20 border border-rose-500/20">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-rose-900 dark:text-rose-300">Efficiency Drop if Removed</span>
                  <span className="font-bold text-rose-900 dark:text-rose-200 text-sm">
                    {(selectedBasin.efficiency_drop_if_removed * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-rose-200/50 dark:bg-rose-900/50 h-1.5 rounded-full mt-2 overflow-hidden">
                  <div
                    className="bg-rose-500 h-full rounded-full"
                    style={{ width: `${Math.min(100, selectedBasin.efficiency_drop_if_removed * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
