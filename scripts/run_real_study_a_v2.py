"""
scripts/run_real_study_a_v2.py - Real-Data Study A Clean Run (Part A).
Executes:
  1. Filters out the 6 zero-rainfall coastal cells -> N=97 active cells.
  2. Recomputes p90, p95, p97 extreme events and ES matrices.
  3. Builds network (top 5% links) and evaluates centralities.
  4. Runs node removal experiments (random, degree, betweenness attacks).
  5. Runs size-matched null models (10,000 draws, 2 seeds) and applies Holm-Bonferroni
     correction across the 6 named basins.
  6. Computes hub stability across p90, p95, p97 with coordinates of stable hubs.
Outputs: outputs/real_data_run_v2/
"""

import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
import networkx as nx

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.ktnet.io import load_config
from src.ktnet.grid import save_cells_parquet
from src.ktnet.events import extract_cell_rainfall_series, compute_cell_events, save_events_npz
from src.ktnet.sync import compute_full_es_matrix
from src.ktnet.network import build_climate_network, compute_network_metrics, save_network_outputs
from src.ktnet.robustness import (
    run_node_removal_experiment,
    compute_basin_impact,
    find_critical_nodes
)
from src.ktnet.null_models import run_basin_size_matched_null_experiment


def holm_bonferroni(p_values: List[float]) -> List[float]:
    """
    Applies step-down Holm-Bonferroni correction to a list of p-values.
    """
    m = len(p_values)
    # Pair with original indices
    indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m
    running_max = 0.0

    for rank, (orig_idx, p) in enumerate(indexed_p):
        k = m - rank
        adj_p = min(1.0, p * k)
        running_max = max(running_max, adj_p)
        adjusted[orig_idx] = round(running_max, 5)

    return adjusted


def main():
    print("=============================================================")
    print("    Vyuham Part A: Real-Data Study A Run (v2 Cleanup)        ")
    print("=============================================================\n")

    config = load_config(str(ROOT_DIR / "config.yaml"))
    
    # Target directory: outputs/real_data_run_v2/
    v2_dir = ROOT_DIR / "outputs" / "real_data_run_v2"
    interim_dir = v2_dir / "interim"
    processed_dir = v2_dir / "processed"
    interim_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    real_rain_path = ROOT_DIR / "data" / "raw" / "imd_rainfall_real.npz"
    basins_real_path = ROOT_DIR / "data" / "raw" / "basins_real.geojson"

    # 1. Load real rainfall cube & baseline 103 cells
    rain_data = np.load(real_rain_path)
    rainfall_cube = rain_data["rainfall"]  # (4880, 23, 17)
    lats = rain_data["lats"]
    lons = rain_data["lons"]
    years = rain_data["years"].tolist()
    days_per_year = int(rain_data["days_per_year"])

    # Load 103 cells from real_data_run
    df_cells_103 = pd.read_parquet(ROOT_DIR / "outputs" / "real_data_run" / "interim" / "cells.parquet")

    # Step 1: Identify zero-rainfall cells across the 40-year record
    zero_rain_mask = []
    for _, r in df_cells_103.iterrows():
        lat_i = np.argmin(np.abs(lats - r["lat"]))
        lon_i = np.argmin(np.abs(lons - r["lon"]))
        cell_total = float(rainfall_cube[:, lat_i, lon_i].sum())
        zero_rain_mask.append(cell_total == 0.0)

    zero_rain_mask = np.array(zero_rain_mask)
    zero_cells_df = df_cells_103[zero_rain_mask].copy()
    print(f"Identified {len(zero_cells_df)} cells with zero rainfall across the entire 40-year record:")
    for _, r in zero_cells_df.iterrows():
        print(f"  - Cell {r['cell_id']} ({r['lat']}°N, {r['lon']}°E, {r['basin_name']})")

    # Filter out these 6 cells -> 97 active land cells
    df_cells_97 = df_cells_103[~zero_rain_mask].copy().reset_index(drop=True)
    out_cells_path = interim_dir / "cells.parquet"
    save_cells_parquet(df_cells_97, str(out_cells_path))
    print(f"\nFiltered active network size: {len(df_cells_97)} nodes (saved to {out_cells_path})")

    print("\nActive Basin Distribution (N=97 cells):")
    print(df_cells_97["basin_name"].value_counts().to_string())

    # Step 2: Extract extreme precipitation events across p90, p95, p97
    print("\n>>> Extracting Extreme Events for N=97 cells (JJAS 1981-2020)...")
    cell_rain = extract_cell_rainfall_series(rainfall_cube, lats, lons, df_cells_97)
    event_data = compute_cell_events(cell_rain, config, years, days_per_year)

    out_events_path = interim_dir / "events.npz"
    save_events_npz(event_data, str(out_events_path))
    for p in [90, 95, 97]:
        tot = sum(len(arr) for arr in event_data["events_by_pct"][p])
        print(f"  * {p}th percentile: total {tot} events, avg {tot/len(df_cells_97):.1f} events/cell.")

    # Step 3: Compute Event Synchronization Matrix for p95
    print("\n>>> Computing 97x97 Event Synchronization Matrix (p95)...")
    n_nodes = len(df_cells_97)
    series_95 = [event_data["events_by_pct"][95][i] for i in range(n_nodes)]
    t0 = time.time()
    es_matrix_95 = compute_full_es_matrix(series_95, max_lag=10.0)
    print(f"ES matrix computed in {time.time()-t0:.2f}s. Min={es_matrix_95.min():.4f}, Max={es_matrix_95.max():.4f}, Mean={es_matrix_95.mean():.4f}")
    out_es_path = interim_dir / "es_matrix.npy"
    np.save(out_es_path, es_matrix_95)

    # Step 4: Build Climate Network (Top 5% links)
    print("\n>>> Building Climate Network (Top 5% links)...")
    cell_ids_97 = df_cells_97["cell_id"].tolist()
    G, links_list, cutoff = build_climate_network(es_matrix_95, cell_ids_97, link_fraction=0.05)
    print(f"Real v2 Climate Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges (Q cutoff = {cutoff:.4f})")

    df_metrics = compute_network_metrics(G, cell_ids_97, max_iter=1000, tol=1e-6)
    out_graphml = processed_dir / "network.graphml"
    out_metrics = processed_dir / "metrics.parquet"
    save_network_outputs(G, df_metrics, str(out_graphml), str(out_metrics))

    df_metrics_merged = pd.merge(df_cells_97[["cell_id", "lat", "lon", "basin_name"]], df_metrics, on="cell_id")

    print("\nTop 5 Hubs by Degree Centrality (N=97 network):")
    top_deg = df_metrics_merged.sort_values(by="degree", ascending=False).head(5)
    for _, r in top_deg.iterrows():
        print(f"  - Cell {r['cell_id']} ({r['lat']}°N, {r['lon']}°E, {r['basin_name']}): degree={r['degree']:.4f}, bet={r['betweenness']:.4f}, eig={r['eigenvector']:.4f}")

    print("\nTop 5 Hubs by Betweenness Centrality (N=97 network):")
    top_bet = df_metrics_merged.sort_values(by="betweenness", ascending=False).head(5)
    for _, r in top_bet.iterrows():
        print(f"  - Cell {r['cell_id']} ({r['lat']}°N, {r['lon']}°E, {r['basin_name']}): bet={r['betweenness']:.4f}, degree={r['degree']:.4f}, eig={r['eigenvector']:.4f}")

    # Step 5: Study A Robustness (Random vs Degree vs Betweenness attacks)
    print("\n>>> Study A Robustness Degradation Experiments...")
    fractions = np.arange(0.0, 0.50 + 1e-5, 0.01)
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
    out_rob = processed_dir / "robustness.parquet"
    rob_df.to_parquet(out_rob, index=False)

    print("\nLCC Degradation at Standard Attack Checkpoints:")
    for f_target in [0.05, 0.10, 0.20, 0.30]:
        idx = int(np.argmin(np.abs(rob_df["fraction_removed"] - f_target)))
        f_val = rob_df.loc[idx, "fraction_removed"]
        r_lcc = rob_df.loc[idx, "random_lcc_mean"]
        d_lcc = rob_df.loc[idx, "degree_lcc"]
        b_lcc = rob_df.loc[idx, "betweenness_lcc"]
        print(f"  * Removal {f_val*100:4.1f}%: Random LCC = {r_lcc*100:5.1f}% | Degree Attack LCC = {d_lcc*100:5.1f}% | Betweenness Attack LCC = {b_lcc*100:5.1f}%")

    # Step 6: Basin Impacts & Null Models with Holm-Bonferroni Correction
    print("\n>>> Basin Removal Impacts & Size-Matched Null Models (10,000 draws, 2 seeds)...")
    df_basin_impact = compute_basin_impact(G, df_cells_97)
    out_bi = processed_dir / "basin_impact.parquet"
    df_basin_impact.to_parquet(out_bi, index=False)

    seeds = [42, 999]
    for s in seeds:
        print(f"\n--- Running 10,000 Null Draws with Seed={s} ---")
        summary_df, _ = run_basin_size_matched_null_experiment(
            G, df_cells_97, n_draws=10000, seed=s
        )

        # Filter to the 6 named basins (exclude 'other' / Coastal Buffer)
        named_mask = summary_df["basin_id"] != "other"
        named_df = summary_df[named_mask].copy().reset_index(drop=True)

        # Apply Holm correction
        raw_scattered_p = named_df["scattered_lcc_pvalue"].tolist()
        raw_contiguous_p = named_df["contiguous_lcc_pvalue"].tolist()

        named_df["scattered_holm_pvalue"] = holm_bonferroni(raw_scattered_p)
        named_df["contiguous_holm_pvalue"] = holm_bonferroni(raw_contiguous_p)

        # Save both full and named tables
        summary_df.to_csv(processed_dir / f"basin_null_all_seed_{s}.csv", index=False)
        named_df.to_csv(processed_dir / f"basin_null_named_holm_seed_{s}.csv", index=False)

        print(f"Results for Seed {s} (6 Named Basins, Holm Corrected):")
        for _, r in named_df.iterrows():
            print(f"  - {r['basin_name']:22s} (k={int(r['n_cells']):2d}): Obs LCC Drop={r['observed_lcc_drop']*100:5.2f}% | "
                  f"Scattered Null: mean={r['scattered_lcc_mean']*100:5.2f}% [5-95%: {r['scattered_lcc_p05']*100:4.1f}-{r['scattered_lcc_p95']*100:4.1f}%], raw_p={r['scattered_lcc_pvalue']:.4f}, holm_p={r['scattered_holm_pvalue']:.4f} | "
                  f"Contiguous Null: mean={r['contiguous_lcc_mean']*100:5.2f}% [5-95%: {r['contiguous_lcc_p05']*100:4.1f}-{r['contiguous_lcc_p95']*100:4.1f}%], raw_p={r['contiguous_lcc_pvalue']:.4f}, holm_p={r['contiguous_holm_pvalue']:.4f}")

    # Step 7: Hub Stability Across p90, p95, p97 on the N=97 network
    print("\n>>> Hub Stability Across Thresholds (p90, p95, p97)...")
    hub_data = {}
    for p in [90, 95, 97]:
        series_p = [event_data["events_by_pct"][p][i] for i in range(n_nodes)]
        es_p = compute_full_es_matrix(series_p, max_lag=10.0)
        Gp, _, cut_p = build_climate_network(es_p, cell_ids_97, link_fraction=0.05)
        mp = compute_network_metrics(Gp, cell_ids_97)
        mp_merged = pd.merge(df_cells_97[["cell_id", "lat", "lon", "basin_name"]], mp, on="cell_id")
        
        top10_d = mp_merged.sort_values(by="degree", ascending=False).head(10)
        top10_b = mp_merged.sort_values(by="betweenness", ascending=False).head(10)
        hub_data[p] = {
            "top10_deg": top10_d,
            "top10_bet": top10_b
        }

    deg_sets = {p: set(hub_data[p]["top10_deg"]["cell_id"]) for p in [90, 95, 97]}
    bet_sets = {p: set(hub_data[p]["top10_bet"]["cell_id"]) for p in [90, 95, 97]}

    print("\nTop 10 Degree Hub Overlaps:")
    print(f"  * p90 & p95: {len(deg_sets[90] & deg_sets[95])}/10 nodes -> {deg_sets[90] & deg_sets[95]}")
    print(f"  * p95 & p97: {len(deg_sets[95] & deg_sets[97])}/10 nodes -> {deg_sets[95] & deg_sets[97]}")
    print(f"  * p90 & p97: {len(deg_sets[90] & deg_sets[97])}/10 nodes -> {deg_sets[90] & deg_sets[97]}")
    stable_deg = deg_sets[90] & deg_sets[95] & deg_sets[97]
    print(f"  * Stable across ALL THREE (p90, p95, p97): {len(stable_deg)} nodes -> {stable_deg}")
    print("    Coordinates of Stable Degree Hubs:")
    for cid in stable_deg:
        row = df_cells_97[df_cells_97["cell_id"] == cid].iloc[0]
        print(f"      - {cid}: ({row['lat']}°N, {row['lon']}°E), Basin: {row['basin_name']}")

    print("\nTop 10 Betweenness Hub Overlaps:")
    print(f"  * p90 & p95: {len(bet_sets[90] & bet_sets[95])}/10 nodes -> {bet_sets[90] & bet_sets[95]}")
    print(f"  * p95 & p97: {len(bet_sets[95] & bet_sets[97])}/10 nodes -> {bet_sets[95] & bet_sets[97]}")
    print(f"  * p90 & p97: {len(bet_sets[90] & bet_sets[97])}/10 nodes -> {bet_sets[90] & bet_sets[97]}")
    stable_bet = bet_sets[90] & bet_sets[95] & bet_sets[97]
    print(f"  * Stable across ALL THREE (p90, p95, p97): {len(stable_bet)} nodes -> {stable_bet}")
    print("    Coordinates of Stable Betweenness Hubs:")
    for cid in stable_bet:
        row = df_cells_97[df_cells_97["cell_id"] == cid].iloc[0]
        print(f"      - {cid}: ({row['lat']}°N, {row['lon']}°E), Basin: {row['basin_name']}")

    print("\n=============================================================")
    print("    Part A: Real-Data Study A v2 Completed Successfully!     ")
    print("=============================================================\n")


if __name__ == "__main__":
    main()
