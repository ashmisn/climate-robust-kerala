import React from 'react';
import { useApp } from '../state/AppContext';
import { StatCard } from '../components/StatCard';
import { MapView } from '../components/MapView';
import { Grid, Share2, Waves, TrendingUp, Info, ArrowRight } from 'lucide-react';
import { formatMetricName } from '../lib/colors';

export const Overview: React.FC = () => {
  const { data, activeMetric, setActivePage } = useApp();

  if (!data) return null;

  // Top basin by impact
  const topBasin = [...data.basins.features].sort(
    (a, b) => a.properties.impact_rank - b.properties.impact_rank
  )[0]?.properties;

  // Strongest correlation with landslide density
  const overallStats = data.landslideStats.overall;
  let strongestMetric = 'betweenness';
  let maxAbsRho = 0;
  let strongestRho = 0;
  let strongestP = 1;

  Object.entries(overallStats).forEach(([metric, stat]) => {
    if (Math.abs(stat.rho) > maxAbsRho) {
      maxAbsRho = Math.abs(stat.rho);
      strongestMetric = metric;
      strongestRho = stat.rho;
      strongestP = stat.p;
    }
  });

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-emerald-900 to-teal-950 text-white rounded-2xl p-6 shadow-md border border-emerald-800/40 relative overflow-hidden">
        <div className="relative z-10 max-w-3xl space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-300 uppercase tracking-wider">
            <span>Spatial Complex Systems</span> • <span>Kerala & Western Ghats</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight">
            Kerala Climate Network — Vyuham
          </h1>
          <p className="text-slate-300 text-xs md:text-sm leading-relaxed">
            Investigating synchronized extreme monsoon precipitation patterns (1991–2020),
            drainage basin topological robustness (Study A), and empirical validation against the 2018 catastrophic landslide disaster (Study B).
          </p>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
        <StatCard
          title="Grid Cells"
          value={data.meta.n_cells}
          subtitle="0.25° (~27 km) resolution"
          icon={Grid}
        />
        <StatCard
          title="Network Links"
          value={data.meta.n_links}
          subtitle={`Top ${(data.meta.link_fraction * 100).toFixed(0)}% synchronized pairs`}
          icon={Share2}
        />
        <StatCard
          title="Critical Basin"
          value={topBasin ? topBasin.name : "Periyar"}
          subtitle={topBasin ? `Rank #${topBasin.impact_rank} • ${topBasin.n_cells} cells` : "Top structural impact"}
          icon={Waves}
        />
        <StatCard
          title="Strongest Correlation"
          value={`ρ = ${strongestRho > 0 ? '+' : ''}${strongestRho.toFixed(2)}`}
          subtitle={`${formatMetricName(strongestMetric)} (p=${strongestP.toFixed(3)})`}
          icon={TrendingUp}
        />
      </div>

      {/* Key Findings Callout (generated dynamically from data) */}
      <div className="bg-emerald-50/70 dark:bg-emerald-950/20 border border-emerald-500/20 rounded-xl p-4 md:p-5 flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-800 dark:text-emerald-300">
            <Info className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Key Research Findings</span>
          </div>
          <p className="text-xs md:text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
            • <strong>Study A (Basin Robustness):</strong> Targeted disconnection of the <strong>{topBasin?.name}</strong> basin induces a <strong>{(topBasin?.lcc_drop_if_removed! * 100).toFixed(1)}% drop</strong> in the largest connected component, showing high topological criticality for interstate rainfall synchronization.
          </p>
          <p className="text-xs md:text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
            • <strong>Study B (Landslide Validation):</strong> Network <strong>{formatMetricName(strongestMetric)}</strong> exhibits a statistically robust Spearman correlation (<strong>ρ = {strongestRho.toFixed(2)}</strong>, 95% CI: [{overallStats[strongestMetric]?.ci_low.toFixed(2)}, {overallStats[strongestMetric]?.ci_high.toFixed(2)}]) with 2018 landslide occurrences.
          </p>
        </div>

        <button
          onClick={() => setActivePage('robustness')}
          className="shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 text-xs font-semibold shadow-xs transition-colors"
        >
          Explore Study A <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Main Map Card */}
      <div className="bg-white dark:bg-slate-900 rounded-xl p-4 md:p-5 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
              Spatial Synchronized Rainfall Network
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Choropleth styled by {formatMetricName(activeMetric)}. Toggle layers or click any cell for localized telemetry.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActivePage('network')}
              className="text-xs font-medium text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1"
            >
              Open Full Network Explorer <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        <MapView heightClass="h-[520px]" showLinksDefault={true} />
      </div>
    </div>
  );
};
