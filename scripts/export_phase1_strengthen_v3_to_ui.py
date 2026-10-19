"""
scripts/export_phase1_strengthen_v3_to_ui.py - Updates web/public/data/ with Phase 1 Strengthen v3 data.
Generates:
  - web/public/data/cells.geojson (97 cells with independent terrain and rainfall fields)
  - web/public/data/links.json (232 real edges)
  - web/public/data/meta.json (97 cells, 232 links, updated provenance)
  - web/public/data/landslide_stats.json (full strengthened schema: all_97 and kerala_48,
      CIs, permutation p, spatial CV model comparison, rainfall controls, point-level test)
"""

import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import networkx as nx

ROOT_DIR = Path(__file__).resolve().parent.parent
STRENGTHEN_DIR = ROOT_DIR / "outputs" / "phase1_strengthen_v3"
REAL_V2_DIR = ROOT_DIR / "outputs" / "real_data_run_v2"
WEB_DATA_DIR = ROOT_DIR / "web" / "public" / "data"

def main():
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load results.json and parquet
    with open(STRENGTHEN_DIR / "results.json", "r", encoding="utf-8") as f:
        strengthen_results = json.load(f)

    df = pd.read_parquet(STRENGTHEN_DIR / "landslide_stats_independent_terrain.parquet")
    print(f"Loaded parquet: {len(df)} cells, {df['is_kerala_50'].sum()} Kerala cells.")

    # 2. Update meta.json
    meta_path = WEB_DATA_DIR / "meta.json"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    meta["n_cells"] = 97
    meta["n_links"] = 232
    meta["generated_at"] = datetime.now(timezone.utc).isoformat()
    meta["provenance"]["landslides"] = "GSI 2018 Catastrophic Landslide Inventory (4,728 initiation points)"
    meta["provenance"]["dem"] = "CGIAR SRTM 90m v4.1 Seamless GeoTIFF Mosaic (independent terrain)"

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("Updated: web/public/data/meta.json (97 cells, 232 links)")

    # 3. Update links.json (232 links)
    G = nx.read_graphml(REAL_V2_DIR / "processed" / "network.graphml")
    links_list = []
    for u, v, d in G.edges(data=True):
        links_list.append({
            "source": str(u),
            "target": str(v),
            "weight": float(d.get("weight", 1.0))
        })
    with open(WEB_DATA_DIR / "links.json", "w", encoding="utf-8") as f:
        json.dump(links_list, f, indent=2)
    print(f"Updated: web/public/data/links.json ({len(links_list)} links)")

    # 4. Update cells.geojson (97 cells with independent terrain & rainfall)
    features = []
    for _, r in df.iterrows():
        coords = r["polygon_coords"]
        if isinstance(coords, str):
            coords = json.loads(coords)
        elif hasattr(coords, "tolist"):
            coords = coords.tolist()

        feat = {
            "type": "Feature",
            "properties": {
                "cell_id": str(r["cell_id"]),
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "basin_id": str(r["basin_id"]),
                "basin_name": str(r["basin_name"]),
                # Terrain fields
                "mean_slope": float(r["slope_dem_mean"]), # Updated to independent DEM mean slope
                "max_slope": float(r["max_slope"]),
                "slope_dem_mean": float(r["slope_dem_mean"]),
                "slope_dem_p90": float(r["slope_dem_p90"]),
                "frac_pixels_over_25deg": float(r["frac_pixels_over_25deg"]),
                "elev_mean": float(r["elev_mean"]),
                "slope_dem_class": str(r["slope_dem_class"]),
                "slope_at_landslides": float(r["slope_at_landslides"]) if not np.isnan(r["slope_at_landslides"]) else None,
                # Landslide counts & density
                "landslide_count_2018": int(r["landslide_count_2018"]),
                "landslide_density": float(r["landslide_density"]),
                "is_kerala_50": bool(r["is_kerala_50"]),
                "kerala_area_frac": float(r["kerala_area_frac"]),
                # Rainfall
                "extreme_days_aug2018": int(r["extreme_days_aug2018"]),
                "aug2018_rain_mm": float(r["aug2018_rain_mm"]),
                "aug2018_extreme_days": int(r["aug2018_extreme_days"]),
                # Centrality metrics
                "degree": float(r["degree"]),
                "betweenness": float(r["betweenness"]),
                "clustering": float(r["clustering"]),
                "eigenvector": float(r["eigenvector"]),
                # 2018 event network metrics
                "degree_2018": float(r["degree_2018"]),
                "betweenness_2018": float(r["betweenness_2018"]),
                "clustering_2018": float(r["clustering_2018"]),
                "eigenvector_2018": float(r["eigenvector_2018"])
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        }
        features.append(feat)

    cells_fc = {"type": "FeatureCollection", "features": features}
    with open(WEB_DATA_DIR / "cells.geojson", "w", encoding="utf-8") as f:
        json.dump(cells_fc, f, indent=2)
    print(f"Updated: web/public/data/cells.geojson ({len(features)} cells)")

    # 5. Build landslide_stats.json
    # Backward-compatible `overall`: use kerala_48 plain spearman + bootstrap CI
    k48_metrics = strengthen_results["step_2_centrality_reanalysis"]["kerala_48_cells"]["metrics"]
    overall_compat = {}
    for m in ["degree", "betweenness", "clustering", "eigenvector"]:
        m_data = k48_metrics[m]
        overall_compat[m] = {
            "rho": round(m_data["plain_rho"], 4),
            "p": round(m_data["plain_p_raw"], 4),
            "ci_low": round(m_data["plain_ci_95"][0], 4),
            "ci_high": round(m_data["plain_ci_95"][1], 4),
            "holm_p": round(m_data["plain_p_holm"], 4),
            # Also store slope-controlled partial rho directly
            "partial_rho": round(m_data["partial_rho"], 4),
            "partial_perm_p": round(m_data["partial_perm_p_raw"], 4),
            "partial_perm_p_holm": round(m_data["partial_perm_p_holm"], 4),
            "spatial_ci_075": [
                m_data["spatial_bootstrap_cis"]["block_0.75deg"]["ci_low"],
                m_data["spatial_bootstrap_cis"]["block_0.75deg"]["ci_high"]
            ]
        }

    # Backward-compatible `by_slope_class`: format from k48 slope_strata
    by_slope_class_compat = []
    k48_strata = strengthen_results["step_2_centrality_reanalysis"]["kerala_48_cells"]["slope_strata"]
    for sc, sc_info in k48_strata.items():
        n = sc_info["n_cells"]
        for m, s in sc_info["metrics"].items():
            by_slope_class_compat.append({
                "class": sc,
                "n": n,
                "metric": m,
                "rho": round(s["rho"], 4),
                "p": round(s["p_value"], 4)
            })

    # Scatter points with independent terrain and rainfall
    scatter_points = []
    for _, r in df.iterrows():
        scatter_points.append({
            "cell_id": str(r["cell_id"]),
            "density": round(float(r["landslide_density"]), 5),
            "slope": round(float(r["slope_dem_mean"]), 2),
            "slope_dem_mean": round(float(r["slope_dem_mean"]), 2),
            "slope_dem_p90": round(float(r["slope_dem_p90"]), 2),
            "elev_mean": round(float(r["elev_mean"]), 1),
            "slope_class": str(r["slope_dem_class"]),
            "is_kerala_50": bool(r["is_kerala_50"]),
            "aug2018_rain_mm": round(float(r["aug2018_rain_mm"]), 1),
            "aug2018_extreme_days": int(r["aug2018_extreme_days"]),
            "degree": round(float(r["degree"]), 4),
            "betweenness": round(float(r["betweenness"]), 4),
            "clustering": round(float(r["clustering"]), 4),
            "eigenvector": round(float(r["eigenvector"]), 4),
            "extreme_days_aug2018": int(r["extreme_days_aug2018"])
        })

    landslide_stats_full = {
        "status": "complete",
        "description": "Strengthened Study B Landslide Validation with Independent CGIAR SRTM 90m Terrain Control",
        "overall": overall_compat,
        "by_slope_class": by_slope_class_compat,
        "scatter": scatter_points,
        # Extended schema for deep UI exploration
        "cell_sets": {
            "kerala_48": strengthen_results["step_2_centrality_reanalysis"]["kerala_48_cells"],
            "all_97": strengthen_results["step_2_centrality_reanalysis"]["all_97_cells"]
        },
        "model_comparison": strengthen_results["step_2_cv_model_comparison"],
        "rainfall_controls": strengthen_results["step_2_event_rainfall"],
        "point_level_auc": strengthen_results["step_2_point_level_test"],
        "exploratory_2018_network": strengthen_results["step_2_exploratory_2018_network"],
        "audit": strengthen_results["step_0_audit"]
    }

    with open(WEB_DATA_DIR / "landslide_stats.json", "w", encoding="utf-8") as f:
        json.dump(landslide_stats_full, f, indent=2)
    print("Updated: web/public/data/landslide_stats.json")

if __name__ == "__main__":
    main()
