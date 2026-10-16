import React from 'react';
import { useApp } from '../state/AppContext';
import { MapView } from '../components/MapView';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';
import { Waves, Droplet, ArrowUpDown } from 'lucide-react';

export const BasinsPage: React.FC = () => {
  const { data, selectedBasin, setSelectedBasin, setSelectedCell } = useApp();

  if (!data) return null;

  // Prepare basin bar chart data
  const basinData = [...data.basins.features]
    .map((b) => ({
      name: b.properties.name,
      basin_id: b.properties.basin_id,
      rank: b.properties.impact_rank,
      n_cells: b.properties.n_cells,
      lcc_drop: Number((b.properties.lcc_drop_if_removed * 100).toFixed(1)),
      efficiency_drop: Number((b.properties.efficiency_drop_if_removed * 100).toFixed(1)),
    }))
    .sort((a, b) => a.rank - b.rank);

  // Active or clicked basin
  const activeBasinId = selectedBasin?.basin_id || basinData[0]?.basin_id;
  const activeBasinObj = data.basins.features.find((b) => b.properties.basin_id === activeBasinId)?.properties;

  // Cells belonging to the active basin
  const constituentCells = data.cells.features
    .filter((c) => c.properties.basin_id === activeBasinId)
    .map((c) => c.properties);

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase font-bold px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300">
            Hydrological Units
          </span>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Waves className="w-5 h-5 text-blue-500" />
            River Basin Topological Vulnerability
          </h1>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Evaluating interstate & inter-basin climate teleconnections when entire drainage basins are removed as coherent groups.
        </p>
      </div>

      {/* Bar Chart Card */}
      <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200">
              Basin Removal Impact Ranking
            </h2>
            <p className="text-xs text-slate-400">
              Disruption to network connectivity (LCC drop % and Efficiency drop %) when each basin is removed.
            </p>
          </div>
        </div>

        <div className="h-64 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={basinData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.6} />
              <XAxis dataKey="name" interval={0} angle={-25} textAnchor="end" tick={{ fontSize: 11 }} />
              <YAxis unit="%" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '0.5rem',
                  color: '#fff',
                  fontSize: '12px'
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Bar dataKey="lcc_drop" name="LCC Drop (%)" fill="#0284c7" radius={[4, 4, 0, 0]} />
              <Bar dataKey="efficiency_drop" name="Efficiency Drop (%)" fill="#0d9488" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Map & Basin Inspector Drill-down */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map */}
        <div className="lg:col-span-2 space-y-2">
          <MapView heightClass="h-[520px]" showLinksDefault={false} />
          <div className="text-[11px] text-slate-400">
            Spatial distribution of grid cells. Click any basin below to view its localized centralities.
          </div>
        </div>

        {/* Basin Drill-down Panel */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-xs flex flex-col h-[520px]">
          <div className="border-b border-slate-200 dark:border-slate-800 pb-3 mb-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Selected Drainage Basin
            </span>
            <div className="flex items-center justify-between mt-1">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Droplet className="w-4 h-4 text-blue-500" />
                {activeBasinObj?.name}
              </h3>
              <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/40 px-2 py-0.5 rounded">
                Rank #{activeBasinObj?.impact_rank}
              </span>
            </div>

            {/* Basin Selector Pills */}
            <div className="flex flex-wrap gap-1 mt-3">
              {basinData.map((b) => (
                <button
                  key={b.basin_id}
                  onClick={() => {
                    const feat = data.basins.features.find((f) => f.properties.basin_id === b.basin_id);
                    if (feat) setSelectedBasin(feat.properties);
                  }}
                  className={`text-[11px] px-2 py-0.5 rounded transition-colors ${
                    activeBasinId === b.basin_id
                      ? 'bg-blue-600 text-white font-semibold'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                  }`}
                >
                  {b.name}
                </button>
              ))}
            </div>
          </div>

          <div className="text-xs font-semibold text-slate-600 dark:text-slate-300 mb-2">
            Constituent Cells ({constituentCells.length}):
          </div>

          <div className="overflow-y-auto flex-1 space-y-2 pr-1">
            {constituentCells.map((c) => (
              <div
                key={c.cell_id}
                onClick={() => setSelectedCell(c)}
                className="p-2.5 rounded-lg border border-slate-200/60 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer text-xs transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">{c.cell_id}</span>
                  <span className="text-[11px] text-slate-400">{c.lat.toFixed(2)}°N, {c.lon.toFixed(2)}°E</span>
                </div>
                <div className="grid grid-cols-3 gap-1 mt-1 text-[11px] text-slate-500">
                  <div>Betw: <strong className="font-mono text-emerald-600">{c.betweenness.toFixed(3)}</strong></div>
                  <div>Deg: <strong className="font-mono text-slate-700 dark:text-slate-300">{c.degree.toFixed(3)}</strong></div>
                  <div>Slope: <strong className="font-mono">{c.mean_slope.toFixed(1)}°</strong></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
