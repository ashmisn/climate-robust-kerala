// Typed loaders for all static files in web/public/data/

import {
  MetaData,
  CellsGeoJSON,
  NetworkLink,
  BasinsGeoJSON,
  RobustnessData,
  CriticalNode,
  SensitivityData,
  LandslideStatsData,
  LandslidePoint
} from "../types/contract";

const BASE_URL = "/data";

export async function fetchJson<T>(filename: string): Promise<T> {
  const res = await fetch(`${BASE_URL}/${filename}`);
  if (!res.ok) {
    throw new Error(`Failed to load ${filename}: status ${res.status}`);
  }
  return res.json();
}

export const loadMeta = (): Promise<MetaData> => fetchJson<MetaData>("meta.json");
export const loadCells = (): Promise<CellsGeoJSON> => fetchJson<CellsGeoJSON>("cells.geojson");
export const loadLinks = (): Promise<NetworkLink[]> => fetchJson<NetworkLink[]>("links.json");
export const loadBasins = (): Promise<BasinsGeoJSON> => fetchJson<BasinsGeoJSON>("basins.geojson");
export const loadRobustness = (): Promise<RobustnessData> => fetchJson<RobustnessData>("robustness.json");
export const loadCriticalNodes = (): Promise<CriticalNode[]> => fetchJson<CriticalNode[]>("critical_nodes.json");
export const loadSensitivity = (): Promise<SensitivityData> => fetchJson<SensitivityData>("sensitivity.json");
export const loadLandslideStats = (): Promise<LandslideStatsData> => fetchJson<LandslideStatsData>("landslide_stats.json");
export const loadLandslidePoints = (): Promise<LandslidePoint[]> => fetchJson<LandslidePoint[]>("landslide_points.json");

export interface FullDataset {
  meta: MetaData;
  cells: CellsGeoJSON;
  links: NetworkLink[];
  basins: BasinsGeoJSON;
  robustness: RobustnessData;
  criticalNodes: CriticalNode[];
  sensitivity: SensitivityData;
  landslideStats: LandslideStatsData;
  landslidePoints: LandslidePoint[];
}

export async function loadAllContractData(): Promise<FullDataset> {
  const [
    meta,
    cells,
    links,
    basins,
    robustness,
    criticalNodes,
    sensitivity,
    landslideStats,
    landslidePoints
  ] = await Promise.all([
    loadMeta(),
    loadCells(),
    loadLinks(),
    loadBasins(),
    loadRobustness(),
    loadCriticalNodes(),
    loadSensitivity(),
    loadLandslideStats(),
    loadLandslidePoints()
  ]);

  return {
    meta,
    cells,
    links,
    basins,
    robustness,
    criticalNodes,
    sensitivity,
    landslideStats,
    landslidePoints
  };
}
