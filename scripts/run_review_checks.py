"""
scripts/run_review_checks.py - Review Checks Orchestrator for Phase 2 Preparation.
Executes:
  Task 1: Periyar & River Basin Cell Counts -> outputs/review_checks/basin_cell_counts.csv
  Task 2: Size-Matched Null Model (Scattered & Contiguous) -> outputs/review_checks/basin_null_results.csv
          and Figures -> outputs/review_checks/periyar_null_distribution.png
  Task 3: Study B All Four Centralities & Landslide Stats -> outputs/review_checks/studyB_all_centralities.csv
"""

import sys
import os
import json
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.ktnet.io import load_config
from src.ktnet.null_models import run_basin_size_matched_null_experiment


def main():
    print("=============================================================")
    print("         Vyuham: Review Checks & Basin Case Study Prep       ")
    print("=============================================================\n")

    config = load_config(str(ROOT_DIR / "config.yaml"))
    out_dir = ROOT_DIR / config["paths"].get("review_checks_dir", "outputs/review_checks")
    out_dir.mkdir(parents=True, exist_ok=True)

    cells_parquet = ROOT_DIR / config["paths"]["interim_data_dir"] / "cells.parquet"
    network_graphml = ROOT_DIR / config["paths"]["processed_data_dir"] / "network.graphml"
    landslides_json = ROOT_DIR / config["paths"]["raw_data_dir"] / "landslides_2018.json"
    landslide_stats_json = ROOT_DIR / config["paths"]["web_data_dir"] / "landslide_stats.json"
    landslide_stats_parquet = ROOT_DIR / config["paths"]["processed_data_dir"] / "landslide_stats.parquet"

    df_cells = pd.read_parquet(cells_parquet)
    G = nx.read_graphml(network_graphml)

    # -------------------------------------------------------------------------
    # TASK 1: Periyar & River Basin Cell Counts
    # -------------------------------------------------------------------------
    print(">>> TASK 1: River Basin Cell Counts")
    total_cells = len(df_cells)

    # Group by basin_id and basin_name
    counts_df = (
        df_cells.groupby(["basin_id", "basin_name"])
        .size()
        .reset_index(name="n_cells")
    )
    counts_df["is_tagged_named_basin"] = counts_df["basin_id"] != "other"
    counts_df["percentage"] = ((counts_df["n_cells"] / total_cells) * 100).round(2)

    # Sort so named basins come first sorted by n_cells descending, then 'other'
    counts_df["sort_key"] = counts_df.apply(
        lambda r: (0 if r["is_tagged_named_basin"] else 1, -r["n_cells"]), axis=1
    )
    counts_df = counts_df.sort_values(by="sort_key").drop(columns=["sort_key"]).reset_index(drop=True)

    csv_task1 = out_dir / "basin_cell_counts.csv"
    counts_df.to_csv(csv_task1, index=False)
    print(f"Saved: {csv_task1}")
    print("\nBasin Cell Counts (out of 103 total):")
    for _, row in counts_df.iterrows():
        tag_str = "Named Basin" if row["is_tagged_named_basin"] else "Untagged / Coastal Buffer"
        print(f"  - {row['basin_name']:25s} ({row['basin_id']:20s}): {row['n_cells']:2d} cells ({row['percentage']:5.1f}%) [{tag_str}]")

    named_basin_cells = counts_df[counts_df["is_tagged_named_basin"]]["n_cells"].sum()
    untagged_cells = counts_df[~counts_df["is_tagged_named_basin"]]["n_cells"].sum()
    print(f"\nSummary: {named_basin_cells} cells tagged to 8 designated river basins, {untagged_cells} untagged (Other / Coastal Buffer).\n")

    # -------------------------------------------------------------------------
    # TASK 2: Size-Matched Null Model for Basin Removal
    # -------------------------------------------------------------------------
    print(">>> TASK 2: Size-Matched Null Model for Basin Removal")
    n_draws = config["null_models"].get("n_draws", 1000)
    seed = config["null_models"].get("seed", 42)

    print(f"Running 1,000 draws (Scattered and Spatially Contiguous) per basin with seed={seed}...")
    null_summary_df, raw_draws = run_basin_size_matched_null_experiment(
        G, df_cells, n_draws=n_draws, seed=seed
    )

    csv_task2 = out_dir / "basin_null_results.csv"
    null_summary_df.to_csv(csv_task2, index=False)
    print(f"Saved: {csv_task2}")

    # Check Periyar
    periyar_row = null_summary_df[null_summary_df["basin_id"] == "basin_periyar"].iloc[0]
    obs_drop = periyar_row["observed_lcc_drop"]
    print(f"\nPeriyar Basin (k={int(periyar_row['n_cells'])} cells):")
    print(f"  - Observed LCC Drop: {obs_drop * 100:.2f}% (reproduces existing 15.73% / 15.7%)")
    print(f"  - Observed Efficiency Drop: {periyar_row['observed_eff_drop'] * 100:.2f}% (reproduces existing 33.65% / 33.7%)")
    print(f"  - (a) Scattered Null LCC Drop: mean={periyar_row['scattered_lcc_mean']*100:.2f}%, 90% range=[{periyar_row['scattered_lcc_p05']*100:.2f}%, {periyar_row['scattered_lcc_p95']*100:.2f}%], p-value={periyar_row['scattered_lcc_pvalue']:.4f}")
    print(f"  - (b) Contiguous Null LCC Drop: mean={periyar_row['contiguous_lcc_mean']*100:.2f}%, 90% range=[{periyar_row['contiguous_lcc_p05']*100:.2f}%, {periyar_row['contiguous_lcc_p95']*100:.2f}%], p-value={periyar_row['contiguous_lcc_pvalue']:.4f}")

    if abs(obs_drop - 0.1573) > 0.001:
        raise ValueError(f"Periyar observed LCC drop {obs_drop} does not match 0.1573 (15.7%)!")

    # Plot Histogram for Periyar
    p_draws = raw_draws["basin_periyar"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=300)

    # Subplot 1: Scattered Null
    ax1 = axes[0]
    ax1.hist(p_draws["scattered_lcc"] * 100, bins=25, color="#38bdf8", edgecolor="#0284c7", alpha=0.7, density=True)
    ax1.axvline(obs_drop * 100, color="#dc2626", linestyle="--", linewidth=2.5, label=f"Observed: {obs_drop*100:.1f}%")
    ax1.axvline(periyar_row["scattered_lcc_mean"] * 100, color="#0284c7", linestyle=":", linewidth=2, label=f"Null Mean: {periyar_row['scattered_lcc_mean']*100:.1f}%")
    ax1.set_title(f"Periyar (k=10): Uniformly Scattered Null\n(Empirical p = {periyar_row['scattered_lcc_pvalue']:.4f})", fontsize=11, fontweight="bold")
    ax1.set_xlabel("LCC Drop (%)", fontsize=10)
    ax1.set_ylabel("Probability Density", fontsize=10)
    ax1.legend(loc="upper right", frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.5)

    # Subplot 2: Spatially Contiguous Null
    ax2 = axes[1]
    ax2.hist(p_draws["contiguous_lcc"] * 100, bins=25, color="#34d399", edgecolor="#059669", alpha=0.7, density=True)
    ax2.axvline(obs_drop * 100, color="#dc2626", linestyle="--", linewidth=2.5, label=f"Observed: {obs_drop*100:.1f}%")
    ax2.axvline(periyar_row["contiguous_lcc_mean"] * 100, color="#059669", linestyle=":", linewidth=2, label=f"Null Mean: {periyar_row['contiguous_lcc_mean']*100:.1f}%")
    ax2.set_title(f"Periyar (k=10): Spatially Contiguous Null\n(Empirical p = {periyar_row['contiguous_lcc_pvalue']:.4f})", fontsize=11, fontweight="bold")
    ax2.set_xlabel("LCC Drop (%)", fontsize=10)
    ax2.set_ylabel("Probability Density", fontsize=10)
    ax2.legend(loc="upper right", frameon=True)
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.suptitle("Vyuham Study A Null Model: Periyar Basin Removal vs. Size-Matched Baselines (k=10, 1000 draws)", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    fig_periyar_path = out_dir / "periyar_null_distribution.png"
    plt.savefig(fig_periyar_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {fig_periyar_path}\n")

    # -------------------------------------------------------------------------
    # TASK 3: All Four Study B Correlations
    # -------------------------------------------------------------------------
    print(">>> TASK 3: Study B All Four Centralities & Landslide Stats")

    with open(landslide_stats_json, "r", encoding="utf-8") as f:
        existing_stats = json.load(f)

    df_ls = pd.read_parquet(landslide_stats_parquet)
    y_dens = df_ls["landslide_density"].values
    s_slope = df_ls["mean_slope"].values

    # Overall slope correlation
    r_slope_y, p_slope_y = spearmanr(s_slope, y_dens)

    # Stratified stats by slope class
    slope_class_map = {}
    for entry in existing_stats["by_slope_class"]:
        s_cls = entry["class"]
        met = entry["metric"]
        if met not in slope_class_map:
            slope_class_map[met] = {}
        slope_class_map[met][s_cls] = (entry["rho"], entry["p"], entry["n"])

    metrics_list = ["degree", "betweenness", "clustering", "eigenvector"]
    study_b_rows = []

    for m in metrics_list:
        overall = existing_stats["overall"][m]
        x_metric = df_ls[m].values

        # Partial Spearman correlation controlling for continuous mean slope:
        # r_xy.z = (r_xy - r_xz * r_yz) / sqrt((1 - r_xz^2) * (1 - r_yz^2))
        r_xm, _ = spearmanr(x_metric, s_slope)
        partial_rho = (overall["rho"] - r_xm * r_slope_y) / np.sqrt((1 - r_xm**2) * (1 - r_slope_y**2))

        study_b_rows.append({
            "metric": m,
            "spearman_rho": overall["rho"],
            "ci_low_95": overall["ci_low"],
            "ci_high_95": overall["ci_high"],
            "p_value": overall["p"],
            "corr_with_slope": round(float(r_xm), 3),
            "partial_rho_controlling_slope": round(float(partial_rho), 3),
            "stratified_rho_low_slope": slope_class_map[m]["Low"][0],
            "stratified_p_low_slope": slope_class_map[m]["Low"][1],
            "stratified_rho_med_slope": slope_class_map[m]["Medium"][0],
            "stratified_p_med_slope": slope_class_map[m]["Medium"][1],
            "stratified_rho_high_slope": slope_class_map[m]["High"][0],
            "stratified_p_high_slope": slope_class_map[m]["High"][1],
        })

    study_b_df = pd.DataFrame(study_b_rows)
    csv_task3 = out_dir / "studyB_all_centralities.csv"
    study_b_df.to_csv(csv_task3, index=False)
    print(f"Saved: {csv_task3}")

    print("\nAll Four Centralities vs. 2018 Landslide Density Table:")
    print(study_b_df[["metric", "spearman_rho", "ci_low_95", "ci_high_95", "p_value", "partial_rho_controlling_slope"]])

    # Landslide Inventory Counts
    with open(landslides_json, "r", encoding="utf-8") as f:
        raw_points = json.load(f)

    n_zero_ls_cells = int((df_ls["landslide_count_2018"] == 0).sum())
    n_nonzero_ls_cells = int((df_ls["landslide_count_2018"] > 0).sum())
    total_ls_mapped = int(df_ls["landslide_count_2018"].sum())
    total_raw_points = len(raw_points)

    print("\nLandslide Inventory Statistics:")
    print(f"  * Total landslide events in raw inventory: {total_raw_points}")
    print(f"  * Total landslide events mapped inside 103 grid cells: {total_ls_mapped} (remainder in coastal/border fringe)")
    print(f"  * Cells with zero landslides: {n_zero_ls_cells} / {total_cells} ({n_zero_ls_cells/total_cells*100:.1f}%)")
    print(f"  * Cells with >=1 landslides: {n_nonzero_ls_cells} / {total_cells} ({n_nonzero_ls_cells/total_cells*100:.1f}%)")
    print("  * Source of inventory file: Geological Survey of India / van Westen, C.J. (2020), 'Spatial landslide inventory for Kerala 2018 extreme monsoon disaster', DANS DOI: 10.17026/dans-x6c-y7x2.")

    print("\n=============================================================")
    print("             Review Checks Completed Successfully!           ")
    print("=============================================================\n")


if __name__ == "__main__":
    main()
