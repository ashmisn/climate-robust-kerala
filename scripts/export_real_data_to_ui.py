"""
scripts/export_real_data_to_ui.py - Export real data pipeline outputs to web/public/data/.
Populates Overview, Network, Robustness, and Basins pages with real 1981-2020 IMD results.
Replaces Landslide page content with 'Pending real inventory and DEM' notice.
"""

import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.ktnet.io import load_config
from src.ktnet.network import build_climate_network, compute_network_metrics
from src.ktnet.robustness import (
    run_node_removal_experiment,
    find_critical_nodes,
    compute_lcc_size
)
from src.ktnet.sync import compute_full_es_matrix


def compute_config_hash(config: dict) -> str:
    cfg_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(cfg_str.encode("utf-8")).hexdigest()[:12]


def main():
    print("=============================================================")
    print("      Vyuham: Re-exporting Real Data to web/public/data/     ")
    print("=============================================================\n")

    config = load_config(str(ROOT_DIR / "config.yaml"))
    
    real_run_dir = ROOT_DIR / "outputs" / "real_data_run"
    interim_dir = real_run_dir / "interim"
    processed_dir = real_run_dir / "processed"
    web_dir = ROOT_DIR / "web" / "public" / "data"
    web_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load cells and metrics
    df_cells = pd.read_parquet(interim_dir / "cells.parquet")
    df_metrics = pd.read_parquet(processed_dir / "metrics.parquet")
    df_joined = pd.merge(df_cells, df_metrics, on="cell_id")

    G = nx.read_graphml(processed_dir / "network.graphml")
    df_basin_impact = pd.read_parquet(processed_dir / "basin_impact.parquet")
    es_matrix = np.load(interim_dir / "es_matrix.npy")
    cell_ids = df_joined["cell_id"].tolist()

    # Re-extract links list
    _, links_list, _ = build_climate_network(es_matrix, cell_ids, link_fraction=0.05)
    print(f"Loaded real network: {len(cell_ids)} cells, {len(links_list)} links.")

    # 1. meta.json
    now_iso = datetime.now(timezone.utc).isoformat()
    meta = {
        "study_area": config.get("study_area", "Kerala (+ Western Ghats buffer)"),
        "period": "1981-2020",
        "season": "JJAS",
        "event_percentile": 95,
        "link_fraction": 0.05,
        "n_cells": len(cell_ids),
        "n_links": len(links_list),
        "generated_at": now_iso,
        "config_hash": compute_config_hash(config),
        "data_mode": "REAL_IMD_1981_2020",
        "provenance": {
            "rainfall": "Real IMD gridded daily rainfall (1981-2020, 0.25 deg)",
            "state_boundary": "GADM 4.1 Kerala State Level-1 boundary",
            "districts": "Census of India 2011 district polygons",
            "river_basins": "Central Water Commission / India-WRIS sub-basins",
            "landslides_and_dem": "Pending real inventory and DEM"
        }
    }
    with open(web_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("Saved: web/public/data/meta.json")

    # 2. cells.geojson
    cell_features = []
    for _, row in df_joined.iterrows():
        coords = json.loads(row["polygon_coords"])
        feat = {
            "type": "Feature",
            "properties": {
                "cell_id": row["cell_id"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "basin_id": row["basin_id"],
                "basin_name": str(row["basin_name"]),
                "mean_slope": 0.0,
                "max_slope": 0.0,
                "landslide_count_2018": 0,
                "landslide_density": 0.0,
                "extreme_days_aug2018": 0,
                "degree": float(row["degree"]),
                "betweenness": float(row["betweenness"]),
                "clustering": float(row["clustering"]),
                "eigenvector": float(row["eigenvector"])
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        }
        cell_features.append(feat)

    cells_fc = {"type": "FeatureCollection", "features": cell_features}
    with open(web_dir / "cells.geojson", "w", encoding="utf-8") as f:
        json.dump(cells_fc, f, indent=2)
    print("Saved: web/public/data/cells.geojson")

    # 3. links.json
    with open(web_dir / "links.json", "w", encoding="utf-8") as f:
        json.dump(links_list, f, indent=2)
    print("Saved: web/public/data/links.json")

    # 4. basins.geojson
    real_basins_path = ROOT_DIR / "data" / "raw" / "basins_real.geojson"
    impact_lookup = {row["basin_id"]: row for _, row in df_basin_impact.iterrows()}
    with open(real_basins_path, "r", encoding="utf-8") as f:
        raw_basins_fc = json.load(f)

    for feat in raw_basins_fc.get("features", []):
        bid = feat["properties"]["basin_id"]
        imp = impact_lookup.get(bid, {})
        feat["properties"] = {
            "basin_id": bid,
            "name": feat["properties"].get("name", bid),
            "n_cells": int(imp.get("n_cells", 0)),
            "impact_rank": int(imp.get("impact_rank", 99)),
            "lcc_drop_if_removed": float(imp.get("lcc_drop_if_removed", 0.0)),
            "efficiency_drop_if_removed": float(imp.get("efficiency_drop_if_removed", 0.0))
        }

    with open(web_dir / "basins.geojson", "w", encoding="utf-8") as f:
        json.dump(raw_basins_fc, f, indent=2)
    print("Saved: web/public/data/basins.geojson")

    # 5. robustness.json
    rob_parquet = pd.read_parquet(processed_dir / "robustness.parquet")
    # Also evaluate efficiency
    step = 0.01
    fractions = rob_parquet["fraction_removed"].tolist()
    rob_results = run_node_removal_experiment(
        G,
        np.array(fractions),
        strategies=["random", "degree", "betweenness"],
        n_random_runs=100,
        seed=42
    )

    robustness_contract = {
        "fractions": fractions,
        "metrics": ["lcc", "efficiency"],
        "strategies": {
            "random": {
                "mean": rob_results["strategies"]["random"]["lcc_mean"],
                "std": rob_results["strategies"]["random"]["lcc_std"],
                "lcc_mean": rob_results["strategies"]["random"]["lcc_mean"],
                "lcc_std": rob_results["strategies"]["random"]["lcc_std"],
                "eff_mean": rob_results["strategies"]["random"]["eff_mean"],
                "eff_std": rob_results["strategies"]["random"]["eff_std"]
            },
            "degree": {
                "lcc": rob_results["strategies"]["degree"]["lcc"],
                "eff": rob_results["strategies"]["degree"]["eff"]
            },
            "betweenness": {
                "lcc": rob_results["strategies"]["betweenness"]["lcc"],
                "eff": rob_results["strategies"]["betweenness"]["eff"]
            }
        }
    }
    with open(web_dir / "robustness.json", "w", encoding="utf-8") as f:
        json.dump(robustness_contract, f, indent=2)
    print("Saved: web/public/data/robustness.json")

    # 6. critical_nodes.json
    critical_nodes = find_critical_nodes(G, df_cells, top_k=15)
    with open(web_dir / "critical_nodes.json", "w", encoding="utf-8") as f:
        json.dump(critical_nodes, f, indent=2)
    print("Saved: web/public/data/critical_nodes.json")

    # 7. sensitivity.json (Hub stability across p90, p95, p97)
    events_npz = np.load(interim_dir / "events.npz", allow_pickle=True)
    networks_by_pct = {}
    metrics_by_pct = {}
    for p in [90, 95, 97]:
        series = [events_npz[f"events_{p}_cell_{i}"] for i in range(len(cell_ids))]
        es_p = compute_full_es_matrix(series, max_lag=10.0)
        Gp, _, _ = build_climate_network(es_p, cell_ids, link_fraction=0.05)
        networks_by_pct[p] = Gp
        metrics_by_pct[p] = compute_network_metrics(Gp, cell_ids)

    sensitivity_dict = {}
    pairs = [("p90_vs_p95", 90, 95), ("p95_vs_p97", 95, 97), ("p90_vs_p97", 90, 97)]
    for label, pA, pB in pairs:
        mA = metrics_by_pct[pA]
        mB = metrics_by_pct[pB]
        top15_A = set(mA.sort_values(by="degree", ascending=False).head(15)["cell_id"])
        top15_B = set(mB.sort_values(by="degree", ascending=False).head(15)["cell_id"])
        overlap_cnt = len(top15_A & top15_B)
        jaccard = overlap_cnt / len(top15_A | top15_B)
        deg_r = float(np.corrcoef(mA["degree"], mB["degree"])[0, 1])
        bet_r = float(np.corrcoef(mA["betweenness"], mB["betweenness"])[0, 1])

        sensitivity_dict[label] = {
            "overlap_count_top15": overlap_cnt,
            "jaccard_overlap": round(jaccard, 3),
            "degree_rank_correlation": round(deg_r, 3),
            "betweenness_rank_correlation": round(bet_r, 3)
        }

    with open(web_dir / "sensitivity.json", "w", encoding="utf-8") as f:
        json.dump(sensitivity_dict, f, indent=2)
    print("Saved: web/public/data/sensitivity.json")

    # 8. landslide_stats.json (Placeholder indicating pending real inventory & DEM)
    landslide_stats_clean = {
        "status": "pending",
        "message": "Pending real inventory and DEM",
        "overall": {
            "degree": {"rho": 0.0, "p": 1.0, "ci_low": 0.0, "ci_high": 0.0},
            "betweenness": {"rho": 0.0, "p": 1.0, "ci_low": 0.0, "ci_high": 0.0},
            "clustering": {"rho": 0.0, "p": 1.0, "ci_low": 0.0, "ci_high": 0.0},
            "eigenvector": {"rho": 0.0, "p": 1.0, "ci_low": 0.0, "ci_high": 0.0}
        },
        "by_slope_class": [],
        "scatter": []
    }
    with open(web_dir / "landslide_stats.json", "w", encoding="utf-8") as f:
        json.dump(landslide_stats_clean, f, indent=2)
    print("Saved: web/public/data/landslide_stats.json")

    # 9. landslide_points.json (Empty array)
    with open(web_dir / "landslide_points.json", "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)
    print("Saved: web/public/data/landslide_points.json")

    print("\n=============================================================")
    print("  All UI Data Contract Files Re-exported Successfully!       ")
    print("=============================================================\n")


if __name__ == "__main__":
    main()
