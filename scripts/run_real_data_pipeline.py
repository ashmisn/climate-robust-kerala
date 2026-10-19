"""
scripts/run_real_data_pipeline.py - Rerun Stages 02-06 using Real IMD Rainfall & Real Basin Boundaries.
All outputs are strictly directed to outputs/real_data_run/ without overwriting baseline outputs.
"""

import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.ktnet.io import load_config
from src.ktnet.grid import build_cell_grid, save_cells_parquet
from src.ktnet.events import extract_cell_rainfall_series, compute_cell_events, save_events_npz
from src.ktnet.sync import compute_full_es_matrix
from src.ktnet.network import build_climate_network, compute_network_metrics, save_network_outputs
from src.ktnet.robustness import (
    run_node_removal_experiment,
    compute_basin_impact,
    find_critical_nodes
)
from src.ktnet.null_models import run_basin_size_matched_null_experiment


def main():
    print("=============================================================")
    print("      Vyuham: Real Data Pipeline Execution (Stages 02-06)   ")
    print("=============================================================\n")

    config = load_config(str(ROOT_DIR / "config.yaml"))
    
    # Define isolated new output directory
    run_dir = ROOT_DIR / "outputs" / "real_data_run"
    interim_dir = run_dir / "interim"
    processed_dir = run_dir / "processed"
    interim_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    real_basins_path = str(ROOT_DIR / "data" / "raw" / "basins_real.geojson")
    real_rain_path = str(ROOT_DIR / "data" / "raw" / "imd_rainfall_real.npz")

    out_cells_path = str(interim_dir / "cells.parquet")
    out_events_path = str(interim_dir / "events.npz")
    out_es_path = str(interim_dir / "es_matrix.npy")
    out_graphml_path = str(processed_dir / "network.graphml")
    out_metrics_path = str(processed_dir / "metrics.parquet")
    out_robustness_path = str(processed_dir / "robustness.parquet")
    out_basin_impact_path = str(processed_dir / "basin_impact.parquet")

    # -------------------------------------------------------------------------
    # STAGE 02: Grid Construction & Real Basin Assignment
    # -------------------------------------------------------------------------
    print(">>> STAGE 02: Building Grid & Tagging Real India-WRIS River Basins")
    df_cells = build_cell_grid(config, basins_geojson_path=real_basins_path)
    save_cells_parquet(df_cells, out_cells_path)
    print(f"Constructed {len(df_cells)} land cells.")
    print("Real River Basin Cell Distribution:")
    print(df_cells["basin_name"].value_counts().to_string())
    print(f"Saved: {out_cells_path}\n")

    # -------------------------------------------------------------------------
    # STAGE 03: Extreme Precipitation Event Extraction (Real IMD 1981-2020)
    # -------------------------------------------------------------------------
    print(">>> STAGE 03: Extracting Extreme Events from Real IMD Rainfall (1981-2020)")
    rain_data = np.load(real_rain_path)
    rainfall_cube = rain_data["rainfall"]
    lats = rain_data["lats"]
    lons = rain_data["lons"]
    years = rain_data["years"].tolist()
    days_per_year = int(rain_data["days_per_year"])

    print(f"Rainfall cube: {rainfall_cube.shape} ({len(years)} years, {days_per_year} days/yr)")
    cell_rain = extract_cell_rainfall_series(rainfall_cube, lats, lons, df_cells)
    event_data = compute_cell_events(cell_rain, config, years, days_per_year)

    for p in [90, 95, 97]:
        total_events = sum(len(arr) for arr in event_data["events_by_pct"][p])
        avg_events = total_events / len(df_cells)
        print(f"  * {p}th percentile: total {total_events} events, avg {avg_events:.1f} events/cell.")

    save_events_npz(event_data, out_events_path)
    print(f"Saved: {out_events_path}\n")

    # -------------------------------------------------------------------------
    # STAGE 04: Event Synchronization Matrix (Real Events)
    # -------------------------------------------------------------------------
    print(">>> STAGE 04: Computing Event Synchronization Matrix")
    n_cells = len(df_cells)
    event_series_list = [event_data["events_by_pct"][95][i] for i in range(n_cells)]
    max_lag = float(config["sync"].get("max_lag_days", 10.0))

    t0 = time.time()
    es_matrix = compute_full_es_matrix(event_series_list, max_lag=max_lag)
    t_es = time.time() - t0
    print(f"Computed {n_cells}x{n_cells} ES matrix in {t_es:.2f} seconds.")
    print(f"ES score range: [{es_matrix.min():.4f}, {es_matrix.max():.4f}], mean: {es_matrix.mean():.4f}")
    np.save(out_es_path, es_matrix)
    print(f"Saved: {out_es_path}\n")

    # -------------------------------------------------------------------------
    # STAGE 05: Climate Network Construction & Metrics
    # -------------------------------------------------------------------------
    print(">>> STAGE 05: Constructing Climate Network (Top 5% Links)")
    cell_ids = df_cells["cell_id"].tolist()
    link_fraction = float(config["network"].get("link_fraction", 0.05))
    max_iter = int(config["network"].get("eigenvector_max_iter", 1000))
    tol = float(config["network"].get("eigenvector_tol", 1e-6))

    G, links_list, cutoff = build_climate_network(es_matrix, cell_ids, link_fraction=link_fraction)
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    print(f"Real Climate Network: {n_nodes} nodes, {n_edges} edges (Q_ij cutoff = {cutoff:.4f})")

    df_metrics = compute_network_metrics(G, cell_ids, max_iter=max_iter, tol=tol)
    save_network_outputs(G, df_metrics, out_graphml_path, out_metrics_path)

    # Report Top Hubs
    df_metrics_merged = pd.merge(df_cells[["cell_id", "lat", "lon", "basin_name"]], df_metrics, on="cell_id")
    print("\nTop 5 Hubs by Degree Centrality:")
    top_deg = df_metrics_merged.sort_values(by="degree", ascending=False).head(5)
    for _, r in top_deg.iterrows():
        print(f"  - Cell {r['cell_id']} ({r['lat']}N, {r['lon']}E, {r['basin_name']}): degree={r['degree']}, bet={r['betweenness']:.4f}, eig={r['eigenvector']:.4f}")

    print("\nTop 5 Hubs by Betweenness Centrality:")
    top_bet = df_metrics_merged.sort_values(by="betweenness", ascending=False).head(5)
    for _, r in top_bet.iterrows():
        print(f"  - Cell {r['cell_id']} ({r['lat']}N, {r['lon']}E, {r['basin_name']}): bet={r['betweenness']:.4f}, degree={r['degree']}, eig={r['eigenvector']:.4f}")

    # -------------------------------------------------------------------------
    # STAGE 06: Study A Robustness & Basin Vulnerability
    # -------------------------------------------------------------------------
    print("\n>>> STAGE 06: Study A Network Robustness (Random vs. Targeted Hub Attacks)")
    step = config["robustness"].get("removal_fraction_step", 0.01)
    max_f = config["robustness"].get("removal_fraction_max", 0.50)
    fractions = np.arange(0.0, max_f + 1e-5, step)

    rob_results = run_node_removal_experiment(
        G,
        fractions,
        strategies=["random", "degree", "betweenness"],
        n_random_runs=100,
        seed=42
    )

    rob_df = pd.DataFrame({
        "fraction_removed": rob_results["fractions"],
        "random_lcc_mean": rob_results["strategies"]["random"]["lcc_mean"],
        "degree_lcc": rob_results["strategies"]["degree"]["lcc"],
        "betweenness_lcc": rob_results["strategies"]["betweenness"]["lcc"]
    })
    rob_df.to_parquet(out_robustness_path, index=False)
    print(f"Saved: {out_robustness_path}")

    # LCC values at key thresholds: 10%, 20%, 30% removal
    print("\nLCC Degradation Profile under Attacks:")
    for f_target in [0.05, 0.10, 0.20, 0.30]:
        idx = int(np.argmin(np.abs(rob_df["fraction_removed"] - f_target)))
        f_val = rob_df.loc[idx, "fraction_removed"]
        r_lcc = rob_df.loc[idx, "random_lcc_mean"]
        d_lcc = rob_df.loc[idx, "degree_lcc"]
        b_lcc = rob_df.loc[idx, "betweenness_lcc"]
        print(f"  * Removal {f_val*100:4.1f}%: Random LCC={r_lcc*100:5.1f}% | Degree Hub Attack LCC={d_lcc*100:5.1f}% | Betweenness Hub Attack LCC={b_lcc*100:5.1f}%")

    # Basin Removal Impacts
    df_basin_impact = compute_basin_impact(G, df_cells)
    df_basin_impact.to_parquet(out_basin_impact_path, index=False)
    print(f"Saved: {out_basin_impact_path}")

    print("\nObserved River Basin Removal Impacts:")
    for _, r in df_basin_impact.iterrows():
        print(f"  - {r['name']:25s} (k={r['n_cells']:2d} cells): LCC drop = {r['lcc_drop_if_removed']*100:5.2f}%, Eff drop = {r['efficiency_drop_if_removed']*100:5.2f}%")

    # -------------------------------------------------------------------------
    # SIZE-MATCHED NULL MODELS: 10,000 DRAWS ACROSS 2 FIXED SEEDS
    # -------------------------------------------------------------------------
    print("\n>>> Size-Matched Null Model Experiments (10,000 Draws, 2 Seeds)")
    seeds = [42, 999]
    null_summaries = {}

    for s in seeds:
        print(f"\n--- Running 10,000 Null Draws with Seed={s} ---")
        t_null0 = time.time()
        summary_df, _ = run_basin_size_matched_null_experiment(
            G, df_cells, n_draws=10000, seed=s
        )
        t_null = time.time() - t_null0
        print(f"Completed 10,000 draws in {t_null:.2f} seconds.")
        
        csv_path = processed_dir / f"basin_null_results_seed_{s}.csv"
        summary_df.to_csv(csv_path, index=False)
        print(f"Saved: {csv_path}")
        null_summaries[s] = summary_df

    # Extract Periyar details
    print("\n=============================================================")
    print("               PERIYAR BASIN NULL MODEL SUMMARY              ")
    print("=============================================================")
    for s in seeds:
        sdf = null_summaries[s]
        p_row = sdf[sdf["basin_id"] == "basin_periyar"].iloc[0]
        k_cells = int(p_row["n_cells"])
        obs_drop = p_row["observed_lcc_drop"]
        sc_mean = p_row["scattered_lcc_mean"]
        sc_p05 = p_row["scattered_lcc_p05"]
        sc_p95 = p_row["scattered_lcc_p95"]
        sc_pval = p_row["scattered_lcc_pvalue"]
        ct_mean = p_row["contiguous_lcc_mean"]
        ct_p05 = p_row["contiguous_lcc_p05"]
        ct_p95 = p_row["contiguous_lcc_p95"]
        ct_pval = p_row["contiguous_lcc_pvalue"]

        print(f"\nSeed {s} (k={k_cells} cells, 10,000 draws):")
        print(f"  * Observed LCC Drop: {obs_drop*100:.2f}%")
        print(f"  * Scattered Null Mean: {sc_mean*100:.2f}% (90% range: [{sc_p05*100:.2f}%, {sc_p95*100:.2f}%]), p-value = {sc_pval:.5f}")
        print(f"  * Contiguous Null Mean: {ct_mean*100:.2f}% (90% range: [{ct_p05*100:.2f}%, {ct_p95*100:.2f}%]), p-value = {ct_pval:.5f}")

    print("\n=============================================================")
    print("      Real Data Pipeline Stages 02-06 Completed Successfully! ")
    print("=============================================================\n")


if __name__ == "__main__":
    main()
