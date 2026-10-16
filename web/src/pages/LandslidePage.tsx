import React, { useState } from 'react';
import { useApp } from '../state/AppContext';
import { MapView } from '../components/MapView';
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';
import { Mountain, AlertTriangle, TrendingUp, Info } from 'lucide-react';
import { formatMetricName } from '../lib/colors';

export const LandslidePage: React.FC = () => {
  const { data, activeMetric, setActiveMetric, setSelectedCell } = useApp();
  const [scatterMetric, setScatterMetric] = useState<'degree' | 'betweenness' | 'clustering' | 'eigenvector'>('betweenness');

  if (!data) return null;

  const lsStats = data.landslideStats;

  // Split scatter data by slope class for colored series
  const lowSlopePoints = lsStats.scatter.filter((d) => d.slope_class === 'Low');
  const medSlopePoints = lsStats.scatter.filter((d) => d.slope_class === 'Medium');
  const highSlopePoints = lsStats.scatter.filter((d) => d.slope_class === 'High');

  const overall = lsStats.overall;

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-bold px-2 py-0.5 rounded bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300">
              Study B
            </span>
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Mountain className="w-5 h-5 text-rose-500" />
              2018 Landslide Validation & Topographic Stratification
            </h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Validating whether extreme-rainfall network centralities correspond to empirical landslide density from the 2018 disaster.
          </p>
        </div>

        {/* Scatter Metric Selector */}
        <div className="flex items-center gap-2 text-xs bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
          <span className="text-slate-500">Scatter Centrality:</span>
          <select
            value={scatterMetric}
            onChange={(e) => setScatterMetric(e.target.value as any)}
            className="bg-transparent text-slate-800 dark:text-slate-100 font-semibold cursor-pointer focus:outline-none"
          >
            <option value="betweenness" className="dark:bg-slate-900">Betweenness</option>
            <option value="degree" className="dark:bg-slate-900">Degree</option>
            <option value="clustering" className="dark:bg-slate-900">Clustering</option>
            <option value="eigenvector" className="dark:bg-slate-900">Eigenvector</option>
          </select>
        </div>
      </div>

      {/* Main Scatter & Map Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scatter Plot */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200">
                Centrality vs 2018 Landslide Density
              </h2>
              <p className="text-xs text-slate-400">
                Stratified into slope tertiles: Low (green), Medium (orange), High (red).
              </p>
            </div>
            <div className="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400">
              ρ = {overall[scatterMetric]?.rho > 0 ? '+' : ''}{overall[scatterMetric]?.rho.toFixed(3)}
            </div>
          </div>

          <div className="h-80 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.6} />
                <XAxis
                  type="number"
                  dataKey={scatterMetric}
                  name={formatMetricName(scatterMetric)}
                  tick={{ fontSize: 11 }}
                  label={{ value: formatMetricName(scatterMetric), position: 'insideBottom', offset: -10, fontSize: 11 }}
                />
                <YAxis
                  type="number"
                  dataKey="density"
                  name="Landslide Density"
                  unit=" pts/km²"
                  tick={{ fontSize: 11 }}
                />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const pt = payload[0].payload;
                      return (
                        <div className="bg-slate-900 text-white p-2.5 rounded-lg text-xs shadow-lg space-y-1 font-sans border border-slate-700">
                          <div className="font-bold text-emerald-400">{pt.cell_id}</div>
                          <div>{formatMetricName(scatterMetric)}: <strong>{pt[scatterMetric]?.toFixed(4)}</strong></div>
                          <div>Landslide Density: <strong>{pt.density?.toFixed(5)}</strong> pts/km²</div>
                          <div>Mean Slope: <strong>{pt.slope?.toFixed(1)}°</strong> ({pt.slope_class} Slope)</div>
                          <div>Aug 2018 Extreme Days: <strong>{pt.extreme_days_aug2018}</strong></div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Scatter name="Low Slope (< 8°)" data={lowSlopePoints} fill="#10b981" />
                <Scatter name="Medium Slope (8° - 18°)" data={medSlopePoints} fill="#f59e0b" />
                <Scatter name="High Slope (> 18°)" data={highSlopePoints} fill="#ef4444" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Map with Landslides Overlay */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-800 shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200">
              Spatial Coincidence Map
            </h2>
            <div className="flex items-center gap-1.5 text-xs text-red-500 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
              2018 Inventory Points (van Westen 2020)
            </div>
          </div>

          <MapView heightClass="h-[340px]" showLandslidesDefault={true} showLinksDefault={false} />
        </div>
      </div>

      {/* Statistical Correlation Table */}
      <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-600" />
            Spearman Rank Correlation Summary with 95% Bootstrap Confidence Intervals
          </h3>
          <p className="text-xs text-slate-400">
            Assessing relationship between each network centrality measure and 2018 empirical landslide density.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-medium">
                <th className="py-2.5 px-3">Centrality Metric</th>
                <th className="py-2.5 px-3">Spearman ρ (Overall)</th>
                <th className="py-2.5 px-3">p-value</th>
                <th className="py-2.5 px-3">95% Bootstrap CI (1000 resamples)</th>
                <th className="py-2.5 px-3">Significance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono">
              {Object.entries(overall).map(([m, stat]) => {
                const isSig = stat.p < 0.05;
                return (
                  <tr key={m} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-sans font-medium text-slate-800 dark:text-slate-200">
                      {formatMetricName(m)}
                    </td>
                    <td className={`py-2.5 px-3 font-bold ${stat.rho > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-600'}`}>
                      {stat.rho > 0 ? '+' : ''}{stat.rho.toFixed(3)}
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 dark:text-slate-400">
                      {stat.p < 0.001 ? '< 0.001' : stat.p.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 dark:text-slate-300">
                      [{stat.ci_low.toFixed(3)}, {stat.ci_high.toFixed(3)}]
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`text-[10px] font-sans font-semibold px-2 py-0.5 rounded-full ${
                        isSig
                          ? 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                      }`}>
                        {isSig ? 'p < 0.05 (Significant)' : 'Not Significant'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Stratification Callout */}
        <div className="bg-slate-50 dark:bg-slate-800/40 p-4 rounded-lg border border-slate-200 dark:border-slate-700/60 text-xs text-slate-600 dark:text-slate-300 space-y-1">
          <div className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-blue-500" />
            Topographic Stratification (Controlling for Slope)
          </div>
          <p>
            When stratified into slope classes, network centralities maintain positive rank correlations in both medium and steep terrain, confirming that extreme precipitation synchronization provides distinct predictive signal beyond static slope angles alone.
          </p>
        </div>
      </div>
    </div>
  );
};
