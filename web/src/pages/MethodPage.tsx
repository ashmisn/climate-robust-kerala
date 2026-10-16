import React from 'react';
import { useApp } from '../state/AppContext';
import { BookOpen, ShieldAlert, Cpu, Database, Network, GitCommit, CheckCircle2 } from 'lucide-react';

export const MethodPage: React.FC = () => {
  const { data } = useApp();

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-5xl mx-auto text-slate-800 dark:text-slate-100">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase font-bold px-2 py-0.5 rounded bg-purple-100 dark:bg-purple-950/60 text-purple-800 dark:text-purple-300">
            Methodology & Provenance
          </span>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-purple-500" />
            Scientific Pipeline & Limitations
          </h1>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Detailed formulation, pipeline execution flow, reproducible parameter hash, and essential scientific caveats.
        </p>
      </div>

      {/* Pipeline Flowchart Diagram */}
      <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
        <h2 className="text-sm font-bold flex items-center gap-2">
          <Cpu className="w-4 h-4 text-emerald-600" />
          End-to-End Pipeline Architecture
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
            <div className="font-bold text-emerald-600 dark:text-emerald-400">1. Data Ingestion</div>
            <p className="text-slate-500 text-[11px]">
              IMD 0.25° Daily Rainfall (1991–2020), India-WRIS River Basins, SRTM 30m DEM, and 2018 Landslide Inventory.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
            <div className="font-bold text-emerald-600 dark:text-emerald-400">2. Event Sync (Numba)</div>
            <p className="text-slate-500 text-[11px]">
              JJAS wet days (≥1 mm), cell 95th percentile threshold, Quian Quiroga dynamic lag delay (τ ≤ 10 days), symmetric Q_ij.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
            <div className="font-bold text-emerald-600 dark:text-emerald-400">3. Studies A & B</div>
            <p className="text-slate-500 text-[11px]">
              Top 5% links, centrality graph, node/basin removal experiments (0–50%), slope-stratified Spearman correlation.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
            <div className="font-bold text-emerald-600 dark:text-emerald-400">4. Static Export</div>
            <p className="text-slate-500 text-[11px]">
              Writes static JSON / GeoJSON contract files into web/public/data/ with zero backend dependencies.
            </p>
          </div>
        </div>
      </div>

      {/* Model Parameters from meta.json */}
      {data?.meta && (
        <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
          <h2 className="text-sm font-bold flex items-center gap-2">
            <Database className="w-4 h-4 text-blue-500" />
            Model & Provenance Parameters (from meta.json)
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="p-2.5 rounded bg-slate-50 dark:bg-slate-800">
              <span className="text-slate-400">Study Area</span>
              <p className="font-medium text-slate-800 dark:text-slate-200 mt-0.5">{data.meta.study_area}</p>
            </div>
            <div className="p-2.5 rounded bg-slate-50 dark:bg-slate-800">
              <span className="text-slate-400">Temporal Normal</span>
              <p className="font-medium text-slate-800 dark:text-slate-200 mt-0.5">{data.meta.period} ({data.meta.season})</p>
            </div>
            <div className="p-2.5 rounded bg-slate-50 dark:bg-slate-800">
              <span className="text-slate-400">Event Percentile</span>
              <p className="font-medium text-slate-800 dark:text-slate-200 mt-0.5">{data.meta.event_percentile}th percentile</p>
            </div>
            <div className="p-2.5 rounded bg-slate-50 dark:bg-slate-800">
              <span className="text-slate-400">Link Density</span>
              <p className="font-medium text-slate-800 dark:text-slate-200 mt-0.5">Top {(data.meta.link_fraction * 100).toFixed(0)}% (Q cutoff)</p>
            </div>
            <div className="p-2.5 rounded bg-slate-50 dark:bg-slate-800">
              <span className="text-slate-400">Active Grid Cells</span>
              <p className="font-mono font-medium text-emerald-600 dark:text-emerald-400 mt-0.5">{data.meta.n_cells} cells</p>
            </div>
            <div className="p-2.5 rounded bg-slate-50 dark:bg-slate-800">
              <span className="text-slate-400">Total Network Edges</span>
              <p className="font-mono font-medium text-emerald-600 dark:text-emerald-400 mt-0.5">{data.meta.n_links} edges</p>
            </div>
            <div className="p-2.5 rounded bg-slate-50 dark:bg-slate-800">
              <span className="text-slate-400">Config SHA256 Hash</span>
              <p className="font-mono font-medium text-purple-600 dark:text-purple-400 mt-0.5">{data.meta.config_hash}</p>
            </div>
            <div className="p-2.5 rounded bg-slate-50 dark:bg-slate-800">
              <span className="text-slate-400">Generated Timestamp</span>
              <p className="font-mono text-[10px] text-slate-600 dark:text-slate-400 mt-0.5 truncate">{data.meta.generated_at}</p>
            </div>
          </div>
        </div>
      )}

      {/* Scientific Sensitivity Summary */}
      {data?.sensitivity && (
        <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
          <h2 className="text-sm font-bold flex items-center gap-2">
            <GitCommit className="w-4 h-4 text-emerald-600" />
            Sensitivity Across Event Percentiles (90 / 95 / 97)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            {Object.entries(data.sensitivity).map(([pair, item]) => (
              <div key={pair} className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
                <div className="font-mono font-bold text-slate-700 dark:text-slate-200">{pair.replace('_', ' ')} Percentiles</div>
                <div className="flex justify-between text-slate-500">
                  <span>Top-15 Node Overlap:</span>
                  <strong className="font-mono text-slate-800 dark:text-slate-200">{item.overlap_count_top15} / 15</strong>
                </div>
                <div className="flex justify-between text-slate-500">
                  <span>Jaccard Index:</span>
                  <strong className="font-mono text-slate-800 dark:text-slate-200">{item.jaccard_overlap.toFixed(2)}</strong>
                </div>
                <div className="flex justify-between text-slate-500">
                  <span>Degree Rank Corr:</span>
                  <strong className="font-mono text-emerald-600 dark:text-emerald-400">{item.degree_rank_correlation.toFixed(2)}</strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explicit Scientific Limitations (Section 10) */}
      <div className="bg-rose-50/70 dark:bg-rose-950/20 border border-rose-500/20 rounded-xl p-5 space-y-3">
        <h2 className="text-sm font-bold text-rose-900 dark:text-rose-300 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-500" />
          Scientific Limitations & Methodological Caveats (Section 10)
        </h2>

        <ul className="space-y-2.5 text-xs text-rose-950/80 dark:text-rose-200/80 leading-relaxed list-disc list-inside">
          <li>
            <strong>Spatial Gauge Interpolation:</strong> IMD grid cells are interpolated from meteorological rain gauges, not physical in-situ stations. Results point to broader geographic regions of synchronization interest for monitoring rather than exact station coordinates.
          </li>
          <li>
            <strong>Resolution & Buffer Necessity:</strong> At 0.25° (~27 km), the geographic bounds of Kerala contain approximately 50 cells. The Western Ghats buffer is essential to make the network sufficiently large for robust topological analysis; basin-level boundaries are approximate.
          </li>
          <li>
            <strong>Geomorphological Confounders:</strong> Landslide density depends strongly on static slope gradient, underlying lithology, soil moisture saturation, and land-use changes. Study B is exploratory, and a moderate or weak correlation is an expected and scientifically valid finding.
          </li>
          <li>
            <strong>Network vs Inundation Physics:</strong> Removal experiments reveal structural importance within the precipitation synchronization topology, not direct hydrological flood routing or immediate physical slope hazard.
          </li>
          <li>
            <strong>Parameter Sensitivity:</strong> Topological network metrics depend on the chosen event threshold percentile (95th) and edge retention fraction (top 5%); the multi-threshold sensitivity analysis quantifies this degree of variance.
          </li>
        </ul>
      </div>
    </div>
  );
};
