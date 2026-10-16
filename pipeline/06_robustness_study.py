"""
pipeline/06_robustness_study.py - Stage 6: Study A Robustness & Basin Vulnerability.
Simulates node removal attacks (random, degree, betweenness) for 0-50% removed,
evaluates whole basin group removals, and calculates sensitivity across thresholds (90/95/97).
Outputs: data/processed/robustness.parquet, basin_impact.parquet, sensitivity.parquet
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ktnet.io import load_config
from src.ktnet.sync import compute_full_es_matrix
from src.ktnet.network import build_climate_network
from src.ktnet.robustness import (
    run_node_removal_experiment,
    compute_basin_impact,
    find_critical_nodes,
    compute_sensitivity_analysis
)

def main():
    print("=== Stage 6: Study A Robustness & Basin Vulnerability ===")
    config = load_config("config.yaml")

    processed_dir = Path(config["paths"]["processed_data_dir"])
    interim_dir = Path(config["paths"]["interim_data_dir"])
    processed_dir.mkdir(parents=True, exist_ok=True)

    cells_parquet_path = interim_dir / "cells.parquet"
    graphml_path = processed_dir / "network.graphml"
    events_npz_path = interim_dir / "events.npz"

    df_cells = pd.read_parquet(cells_parquet_path)
    G = nx.read_graphml(graphml_path)

    # 1. Node removal experiments (0 to 50% removed with step 0.01)
    step = config["robustness"].get("removal_fraction_step", 0.01)
    max_f = config["robustness"].get("removal_fraction_max", 0.50)
    fractions = np.arange(0.0, max_f + 1e-5, step)

    print("Running node removal simulations (Random 100 runs, Degree, Betweenness)...")
    robustness_results = run_node_removal_experiment(
        G,
        fractions,
        strategies=config["robustness"].get("strategies", ["random", "degree", "betweenness"]),
        n_random_runs=config["robustness"].get("random_runs", 100),
        seed=config.get("random_seed", 42)
    )

    # Convert to tabular DataFrame for robustness.parquet
    rob_records = []
    for idx, f in enumerate(robustness_results["fractions"]):
        rob_records.append({
            "fraction_removed": f,
            "random_lcc_mean": robustness_results["strategies"]["random"]["lcc_mean"][idx],
            "random_lcc_std": robustness_results["strategies"]["random"]["lcc_std"][idx],
            "random_eff_mean": robustness_results["strategies"]["random"]["eff_mean"][idx],
            "random_eff_std": robustness_results["strategies"]["random"]["eff_std"][idx],
            "degree_lcc": robustness_results["strategies"]["degree"]["lcc"][idx],
            "degree_eff": robustness_results["strategies"]["degree"]["eff"][idx],
            "betweenness_lcc": robustness_results["strategies"]["betweenness"]["lcc"][idx],
            "betweenness_eff": robustness_results["strategies"]["betweenness"]["eff"][idx],
        })
    df_rob = pd.DataFrame(rob_records)
    df_rob.to_parquet(processed_dir / "robustness.parquet", index=False)

    # 2. Basin removal impact
    print("Evaluating whole basin removal impacts...")
    df_basin_impact = compute_basin_impact(G, df_cells)
    df_basin_impact.to_parquet(processed_dir / "basin_impact.parquet", index=False)
    print("Basin Impact Rankings:")
    print(df_basin_impact[["impact_rank", "basin_id", "name", "n_cells", "lcc_drop_if_removed", "efficiency_drop_if_removed"]])

    # 3. Top 15 critical nodes
    crit_nodes = find_critical_nodes(G, df_cells, top_k=15)
    print(f"Identified {len(crit_nodes)} critical nodes. Top 3: {crit_nodes[:3]}")

    # 4. Sensitivity runs across 90, 95, 97 percentiles
    print("Computing sensitivity across event percentiles (90%, 95%, 97%)...")
    events_data = np.load(events_npz_path)
    n_cells = len(df_cells)
    cell_ids = df_cells["cell_id"].tolist()
    networks_by_pct = {95: G}

    for p in [90, 97]:
        series_p = [events_data[f"events_{p}_cell_{i}"] for i in range(n_cells)]
        es_p = compute_full_es_matrix(series_p, max_lag=config["sync"].get("max_lag_days", 10.0))
        G_p, _, _ = build_climate_network(es_p, cell_ids, link_fraction=config["network"].get("link_fraction", 0.05))
        networks_by_pct[p] = G_p

    sensitivity_res = compute_sensitivity_analysis(networks_by_pct, df_cells)
    df_sens = pd.DataFrame([
        {"comparison": k, **v} for k, v in sensitivity_res.items()
    ])
    df_sens.to_parquet(processed_dir / "sensitivity.parquet", index=False)
    print("Sensitivity Analysis Summary:\n", df_sens)

    print("Stage 6 complete.")

if __name__ == "__main__":
    main()
