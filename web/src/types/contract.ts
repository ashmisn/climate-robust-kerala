// TypeScript interfaces strictly matching Section 4 Data Contract

export interface MetaData {
  study_area: string;
  period: string;
  season: string;
  event_percentile: number;
  link_fraction: number;
  n_cells: number;
  n_links: number;
  generated_at: string;
  config_hash: string;
}

export interface CellProperties {
  cell_id: string;
  lat: number;
  lon: number;
  basin_id: string;
  basin_name?: string;
  mean_slope: number;
  max_slope: number;
  landslide_count_2018: number;
  landslide_density: number;
  extreme_days_aug2018: number;
  degree: number;
  betweenness: number;
  clustering: number;
  eigenvector: number;
}

export interface CellFeature {
  type: "Feature";
  properties: CellProperties;
  geometry: {
    type: "Polygon";
    coordinates: number[][][];
  };
}

export interface CellsGeoJSON {
  type: "FeatureCollection";
  features: CellFeature[];
}

export interface NetworkLink {
  source: string;
  target: string;
  weight: number;
}

export interface BasinProperties {
  basin_id: string;
  name: string;
  n_cells: number;
  impact_rank: number;
  lcc_drop_if_removed: number;
  efficiency_drop_if_removed: number;
}

export interface BasinFeature {
  type: "Feature";
  properties: BasinProperties;
  geometry: {
    type: "Polygon" | "MultiPolygon";
    coordinates: any;
  };
}

export interface BasinsGeoJSON {
  type: "FeatureCollection";
  features: BasinFeature[];
}

export interface RobustnessData {
  fractions: number[];
  metrics: string[];
  strategies: {
    random: {
      mean: number[];
      std: number[];
      lcc_mean?: number[];
      lcc_std?: number[];
      eff_mean?: number[];
      eff_std?: number[];
    };
    degree: {
      lcc: number[];
      eff: number[];
    };
    betweenness: {
      lcc: number[];
      eff: number[];
    };
  };
}

export interface CriticalNode {
  cell_id: string;
  rank: number;
  lcc_drop: number;
  basin_id: string;
}

export interface SensitivityItem {
  overlap_count_top15: number;
  jaccard_overlap: number;
  degree_rank_correlation: number;
  betweenness_rank_correlation: number;
}

export type SensitivityData = Record<string, SensitivityItem>;

export interface LandslideCorrelationStat {
  rho: number;
  p: number;
  ci_low: number;
  ci_high: number;
}

export interface SlopeClassCorrelation {
  class: string;
  n: number;
  metric: string;
  rho: number;
  p: number;
}

export interface ScatterPoint {
  cell_id: string;
  density: number;
  slope: number;
  slope_class?: string;
  degree?: number;
  betweenness?: number;
  clustering?: number;
  eigenvector?: number;
  extreme_days_aug2018?: number;
}

export interface LandslideStatsData {
  overall: Record<string, LandslideCorrelationStat>;
  by_slope_class: SlopeClassCorrelation[];
  scatter: ScatterPoint[];
}

export interface LandslidePoint {
  lat: number;
  lon: number;
}

export type MetricType = "betweenness" | "degree" | "clustering" | "eigenvector" | "landslide_density" | "mean_slope" | "extreme_days_aug2018";
