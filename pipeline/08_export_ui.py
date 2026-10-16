"""
pipeline/08_export_ui.py - Stage 8: Data Contract Serialization.
Assembles outputs from all prior pipeline stages and writes strictly formatted
JSON/GeoJSON files directly into web/public/data/ for the React dashboard.
"""

import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ktnet.io import load_config
from src.ktnet.export import export_all_contract_data
from src.ktnet.robustness import (
    run_node_removal_experiment,
    find_critical_nodes,
    compute_sensitivity_analysis
)
from src.ktnet.landslide import compute_landslide_correlations
from src.ktnet.network import build_climate_network
from src.ktnet.sync import compute_full_es_matrix

def main():
    print("=== Stage 8: UI Data Contract Export ===")
    config = load_config("config.yaml")

    raw_dir = Path(config["paths"]["raw_data_dir"])
    interim_dir = Path(config["paths"]["interim_data_dir"])
    processed_dir = Path(config["paths"]["processed_data_dir"])
    web_dir = Path(config["paths"]["web_data_dir"])

    cells_parquet_path = interim_dir / "cells.parquet"
    graphml_path = processed_dir / "network.graphml"
    basin_impact_path = processed_dir / "basin_impact.parquet"
    sensitivity_path = processed_dir / "sensitivity.parquet"
    basins_raw_geojson = raw_dir / "basins.geojson"
    landslides_raw_json = raw_dir / "landslides_2018.json"
    events_npz_path = interim_dir / "events.npz"
    es_matrix_path = interim_dir / "es_matrix.npy"

    df_cells = pd.read_parquet(cells_parquet_path)
    G = nx.read_graphml(graphml_path)
    df_basin_impact = pd.read_parquet(basin_impact_path)

    # 1. Links list
    es_matrix = np.load(es_matrix_path)
    cell_ids = df_cells["cell_id"].tolist()
    _, links_list, _ = build_climate_network(
        es_matrix,
        cell_ids,
        link_fraction=config["network"].get("link_fraction", 0.05)
    )

    # 2. Robustness data structure
    step = config["robustness"].get("removal_fraction_step", 0.01)
    max_f = config["robustness"].get("removal_fraction_max", 0.50)
    fractions = np.arange(0.0, max_f + 1e-5, step)
    robustness_results = run_node_removal_experiment(
        G,
        fractions,
        strategies=config["robustness"].get("strategies", ["random", "degree", "betweenness"]),
        n_random_runs=config["robustness"].get("random_runs", 100),
        seed=config.get("random_seed", 42)
    )

    # Format robustness object matching contract:
    # { strategies: { random: { mean: [], std: [] }, degree: [], betweenness: [] }, fractions: [...], metrics: ["lcc", "efficiency"] }
    # Let's provide clean accessible keys for both lcc and efficiency
    robustness_contract = {
        "fractions": robustness_results["fractions"],
        "metrics": ["lcc", "efficiency"],
        "strategies": {
            "random": {
                "mean": robustness_results["strategies"]["random"]["lcc_mean"],
                "std": robustness_results["strategies"]["random"]["lcc_std"],
                "lcc_mean": robustness_results["strategies"]["random"]["lcc_mean"],
                "lcc_std": robustness_results["strategies"]["random"]["lcc_std"],
                "eff_mean": robustness_results["strategies"]["random"]["eff_mean"],
                "eff_std": robustness_results["strategies"]["random"]["eff_std"]
            },
            "degree": {
                "lcc": robustness_results["strategies"]["degree"]["lcc"],
                "eff": robustness_results["strategies"]["degree"]["eff"]
            },
            "betweenness": {
                "lcc": robustness_results["strategies"]["betweenness"]["lcc"],
                "eff": robustness_results["strategies"]["betweenness"]["eff"]
            }
        }
    }

    # 3. Critical nodes
    critical_nodes = find_critical_nodes(G, df_cells, top_k=15)

    # 4. Sensitivity results
    df_sens = pd.read_parquet(sensitivity_path)
    sensitivity_dict = {}
    for _, row in df_sens.iterrows():
        k = row["comparison"]
        sensitivity_dict[k] = {
            "overlap_count_top15": int(row["overlap_count_top15"]),
            "jaccard_overlap": float(row["jaccard_overlap"]),
            "degree_rank_correlation": float(row["degree_rank_correlation"]),
            "betweenness_rank_correlation": float(row["betweenness_rank_correlation"])
        }

    # 5. Landslide statistics
    landslide_stats = compute_landslide_correlations(
        df_cells,
        n_bootstrap=config["landslide"].get("bootstrap_ci_samples", 1000)
    )

    # 6. Landslide points
    with open(landslides_raw_json, "r", encoding="utf-8") as f:
        landslide_points = json.load(f)

    # Export all
    print(f"Exporting files to {web_dir}...")
    export_all_contract_data(
        config=config,
        cells_df=df_cells,
        links_list=links_list,
        basins_impact_df=df_basin_impact,
        basins_geojson_path=str(basins_raw_geojson),
        robustness_results=robustness_contract,
        critical_nodes=critical_nodes,
        sensitivity_results=sensitivity_dict,
        landslide_stats=landslide_stats,
        landslide_points=landslide_points,
        output_dir=str(web_dir)
    )

    print("Stage 8 complete: All contract files exported to web/public/data/ successfully.")

if __name__ == "__main__":
    main()
