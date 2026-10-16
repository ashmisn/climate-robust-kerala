import React, { useState, useMemo } from 'react';
import { useApp } from '../state/AppContext';
import { MapView } from '../components/MapView';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  Area
} from 'recharts';
import { ShieldAlert, Play, RotateCcw, AlertTriangle, Layers } from 'lucide-react';

export const RobustnessPage: React.FC = () => {
  const { data, selectedCell, setSelectedCell } = useApp();
  const [activeMetricTab, setActiveMetricTab] = useState<'lcc' | 'efficiency'>('lcc');
  const [removalStrategy, setRemovalStrategy] = useState<'random' | 'degree' | 'betweenness'>('degree');
  const [removalFraction, setRemovalFraction] = useState<number>(0.0);
  const [highlightedCellId, setHighlightedCellId] = useState<string | null>(null);

  if (!data) return null;

  const rob = data.robustness;

  // Prepare chart data series
  const chartData = useMemo(() => {
    return rob.fractions.map((f, i) => {
      if (activeMetricTab === 'lcc') {
        const randMean = rob.strategies.random.lcc_mean ? rob.strategies.random.lcc_mean[i] : rob.strategies.random.mean[i];
        const randStd = rob.strategies.random.lcc_std ? rob.strategies.random.lcc_std[i] : rob.strategies.random.std[i];
        return {
          fraction: (f * 100).toFixed(0) + '%',
          rawFraction: f,
          Random: randMean,
          RandomMin: Math.max(0, randMean - randStd),
          RandomMax: Math.min(1, randMean + randStd),
          Degree: rob.strategies.degree.lcc[i],
          Betweenness: rob.strategies.betweenness.lcc[i],
        };
      } else {
        const randMean = rob.strategies.random.eff_mean ? rob.strategies.random.eff_mean[i] : rob.strategies.random.mean[i];
        const randStd = rob.strategies.random.eff_std ? rob.strategies.random.eff_std[i] : rob.strategies.random.std[i];
        return {
          fraction: (f * 100).toFixed(0) + '%',
          rawFraction: f,
          Random: randMean,
          RandomMin: Math.max(0, randMean - randStd),
          RandomMax: Math.min(1, randMean + randStd),
          Degree: rob.strategies.degree.eff[i],
          Betweenness: rob.strategies.betweenness.eff[i],
        };
      }
    });
  }, [rob, activeMetricTab]);

  // Determine removed cell IDs for visual grey-out on map based on slider
  const removedCellIds = useMemo(() => {
    const set = new Set<string>();
    if (removalFraction <= 0.001) return set;

    const cells = [...data.cells.features].map((f) => f.properties);
    const numToRemove = Math.round(removalFraction * cells.length);

    if (removalStrategy === 'degree') {
      cells.sort((a, b) => b.degree - a.degree);
    } else if (removalStrategy === 'betweenness') {
      cells.sort((a, b) => b.betweenness - a.betweenness);
    } else {
      // Deterministic pseudo-random order
      cells.sort((a, b) => (parseInt(a.cell_id.replace('c_', ''), 10) * 17) % 103 - (parseInt(b.cell_id.replace('c_', ''), 10) * 17) % 103);
    }

    for (let i = 0; i < numToRemove && i < cells.length; i++) {
      set.add(cells[i].cell_id);
    }

    return set;
  }, [data, removalFraction, removalStrategy]);

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-bold px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300">
              Study A
            </span>
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-500" />
              Basin & Network Robustness Analysis
            </h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Simulate percolation breakdown and node removal attacks under random failure versus targeted degree & betweenness disruptions.
          </p>
        </div>

        {/* Metric Selector Tabs */}
        <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-lg border border-slate-200 dark:border-slate-700">
          <button
            onClick={() => setActiveMetricTab('lcc')}
            className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
              activeMetricTab === 'lcc'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs font-semibold'
                : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Largest Connected Component (LCC)
          </button>
          <button
            onClick={() => setActiveMetricTab('efficiency')}
            className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
              activeMetricTab === 'efficiency'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs font-semibold'
                : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Global Efficiency
          </button>
        </div>
      </div>

      {/* Degradation Chart Card */}
      <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200">
              Network Degradation Curve (0–50% Nodes Removed)
            </h2>
            <p className="text-xs text-slate-400">
              Curves start at 1.0 (intact state). Notice how targeted attacks cause rapid fragmentation compared to random loss.
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium">
            <div className="flex items-center gap-1.5 text-slate-500">
              <span className="w-3 h-0.5 bg-slate-400" /> Random (100 runs)
            </div>
            <div className="flex items-center gap-1.5 text-orange-600 dark:text-orange-400">
              <span className="w-3 h-0.5 bg-orange-500" /> Targeted Degree
            </div>
            <div className="flex items-center gap-1.5 text-indigo-600 dark:text-indigo-400">
              <span className="w-3 h-0.5 bg-indigo-500" /> Targeted Betweenness
            </div>
          </div>
        </div>

        <div className="h-72 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.6} />
              <XAxis dataKey="fraction" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 1.05]} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '0.5rem',
                  color: '#fff',
                  fontSize: '12px'
                }}
              />
              <Line
                type="monotone"
                dataKey="Random"
                stroke="#64748b"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="Degree"
                stroke="#f97316"
                strokeWidth={2.5}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="Betweenness"
                stroke="#6366f1"
                strokeWidth={2.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Interactive Removal Simulation & Map */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map with Removal Greying */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-700/60">
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">
                Removal Slider:
              </span>
              <input
                type="range"
                min="0.0"
                max="0.50"
                step="0.02"
                value={removalFraction}
                onChange={(e) => setRemovalFraction(parseFloat(e.target.value))}
                className="w-32 md:w-48 h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
              <span className="text-xs font-mono font-bold text-amber-600 dark:text-amber-400">
                {(removalFraction * 100).toFixed(0)}% Removed ({removedCellIds.size} cells)
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Attack Mode:</span>
              <select
                value={removalStrategy}
                onChange={(e) => setRemovalStrategy(e.target.value as any)}
                className="text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded px-2 py-1 font-medium cursor-pointer"
              >
                <option value="degree">Targeted Degree</option>
                <option value="betweenness">Targeted Betweenness</option>
                <option value="random">Random Failure</option>
              </select>
            </div>
          </div>

          <MapView
            heightClass="h-[500px]"
            removedCellIds={removedCellIds}
            highlightCellId={highlightedCellId}
            showLinksDefault={true}
          />
          <div className="text-[11px] text-slate-400">
            Grayed-out dashed polygons indicate dismantled cells at the current removal fraction.
          </div>
        </div>

        {/* Top 15 Critical Nodes Table */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-xs flex flex-col h-[590px]">
          <div className="border-b border-slate-200 dark:border-slate-800 pb-2 mb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-200 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              Top 15 Critical Nodes
            </h3>
            <p className="text-[11px] text-slate-400">
              Ranked by individual LCC drop when disconnected.
            </p>
          </div>

          <div className="overflow-y-auto flex-1 space-y-1.5 pr-1">
            {data.criticalNodes.map((item) => {
              const isHighlighted = highlightedCellId === item.cell_id;
              return (
                <div
                  key={item.cell_id}
                  onClick={() => {
                    setHighlightedCellId(item.cell_id);
                    const cellFeat = data.cells.features.find((f) => f.properties.cell_id === item.cell_id);
                    if (cellFeat) setSelectedCell(cellFeat.properties);
                  }}
                  className={`p-2.5 rounded-lg text-xs cursor-pointer transition-all border flex items-center justify-between ${
                    isHighlighted
                      ? 'bg-amber-50 dark:bg-amber-950/40 border-amber-500/50 text-amber-900 dark:text-amber-200 font-medium'
                      : 'bg-slate-50/50 dark:bg-slate-800/30 border-slate-200/60 dark:border-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-slate-200 dark:bg-slate-700 text-[10px] font-bold flex items-center justify-center font-mono">
                      {item.rank}
                    </span>
                    <div>
                      <div className="font-mono font-bold">{item.cell_id}</div>
                      <div className="text-[10px] text-slate-400 truncate max-w-[120px]">{item.basin_id}</div>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="font-mono font-bold text-amber-600 dark:text-amber-400">
                      -{(item.lcc_drop * 100).toFixed(1)}%
                    </div>
                    <div className="text-[10px] text-slate-400">LCC Drop</div>
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
