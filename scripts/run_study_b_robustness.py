"""
scripts/run_study_b_robustness.py - Study B Robustness Checks.
Executes:
  1. State boundary tagging (Kerala vs. Western Ghats buffer) and zero-landslide audit.
  2. Kerala-only four-centrality Spearman table with slope control, bootstrap CIs,
     and presence/absence ROC-AUC -> outputs/review_checks/studyB_kerala_only.csv
  3. Study B v2 ladder with extra controls (2018 JJAS rainfall, elevation)
     and spatial-block bootstrap CIs -> outputs/review_checks/studyB_v2.csv
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.ktnet.io import load_config
from src.ktnet.landslide import bootstrap_spearman_ci
from src.ktnet.landslide_controls import (
    tag_kerala_cells,
    extract_cell_2018_jjas_rainfall,
    extract_cell_elevation,
    assign_spatial_blocks,
    partial_spearman_rank_corr,
    compute_roc_auc,
    spatial_block_bootstrap_ci
)


def main():
    print("=============================================================")
    print("           Vyuham: Study B Robustness Checks Pipeline        ")
    print("=============================================================\n")

    config = load_config(str(ROOT_DIR / "config.yaml"))
    out_dir = ROOT_DIR / config["paths"].get("review_checks_dir", "outputs/review_checks")
    out_dir.mkdir(parents=True, exist_ok=True)

    cells_parquet = ROOT_DIR / config["paths"]["interim_data_dir"] / "cells.parquet"
    landslide_stats_parquet = ROOT_DIR / config["paths"]["processed_data_dir"] / "landslide_stats.parquet"
    imd_rainfall_path = ROOT_DIR / config["paths"]["raw_data_dir"] / "imd_rainfall.npz"

    # Prefer processed landslide_stats if available, else interim cells
    if landslide_stats_parquet.exists():
        df_all = pd.read_parquet(landslide_stats_parquet)
    else:
        df_all = pd.read_parquet(cells_parquet)

    total_cells = len(df_all)

    # -------------------------------------------------------------------------
    # STEP 1: Tag Inside vs Outside Kerala Boundary & Audit Zero-Landslide Cells
    # -------------------------------------------------------------------------
    print(">>> STEP 1: Kerala State Boundary Tagging & Zero-Landslide Audit")
    df_tagged = tag_kerala_cells(df_all)

    n_inside = int(df_tagged["inside_kerala"].sum())
    n_outside = total_cells - n_inside

    zero_ls_mask = df_tagged["landslide_count_2018"] == 0
    total_zero_ls = int(zero_ls_mask.sum())
    nonzero_ls_mask = df_tagged["landslide_count_2018"] > 0
    total_nonzero_ls = int(nonzero_ls_mask.sum())

    zero_ls_outside = int((zero_ls_mask & (~df_tagged["inside_kerala"])).sum())
    zero_ls_inside = int((zero_ls_mask & df_tagged["inside_kerala"]).sum())
    nonzero_ls_inside = int((nonzero_ls_mask & df_tagged["inside_kerala"]).sum())
    nonzero_ls_outside = int((nonzero_ls_mask & (~df_tagged["inside_kerala"])).sum())

    print(f"Total Grid Cells: {total_cells}")
    print(f"  - Inside Kerala state boundary: {n_inside} cells ({n_inside/total_cells*100:.1f}%)")
    print(f"  - Outside Kerala (Western Ghats buffer in TN/Karnataka): {n_outside} cells ({n_outside/total_cells*100:.1f}%)")
    print(f"\nZero-Landslide Cells Audit:")
    print(f"  - Total zero-landslide cells: {total_zero_ls} / {total_cells}")
    print(f"  - Zero-landslide cells OUTSIDE Kerala: {zero_ls_outside} / {total_zero_ls} ({zero_ls_outside/total_zero_ls*100:.1f}%)")
    print(f"  - Zero-landslide cells INSIDE Kerala: {zero_ls_inside} / {total_zero_ls} ({zero_ls_inside/total_zero_ls*100:.1f}%)")
    print(f"  - Non-zero landslide cells INSIDE Kerala: {nonzero_ls_inside} / {total_nonzero_ls}")
    print(f"  - Non-zero landslide cells OUTSIDE Kerala: {nonzero_ls_outside} / {total_nonzero_ls} (border fringe)\n")

    # -------------------------------------------------------------------------
    # STEP 2 & 3: Kerala-Only Four-Centrality Spearman Table + AUC Check
    # -------------------------------------------------------------------------
    print(">>> STEP 2 & 3: Kerala-Only Centrality Analysis & Presence/Absence AUC Check")
    df_kerala = df_tagged[df_tagged["inside_kerala"]].copy().reset_index(drop=True)
    n_kerala = len(df_kerala)

    y_dens = df_kerala["landslide_density"].values
    y_binary = (df_kerala["landslide_count_2018"] >= 1).astype(int).values
    s_slope = df_kerala["mean_slope"].values

    r_slope_y, _ = spearmanr(s_slope, y_dens)
    n_bootstrap = int(config["landslide"].get("bootstrap_ci_samples", 1000))
    alpha = float(config["landslide"].get("bootstrap_alpha", 0.05))
    seed = int(config.get("random_seed", 42))

    metrics_list = ["degree", "betweenness", "clustering", "eigenvector"]
    kerala_only_rows = []

    for m in metrics_list:
        x = df_kerala[m].values
        rho, p = spearmanr(x, y_dens)
        ci_low, ci_high = bootstrap_spearman_ci(x, y_dens, n_bootstrap=n_bootstrap, alpha=alpha, seed=seed)
        
        # Continuous slope partial correlation
        r_xm, _ = spearmanr(x, s_slope)
        partial_rho = (rho - r_xm * r_slope_y) / np.sqrt((1 - r_xm**2) * (1 - r_slope_y**2))
        
        # Presence/absence ROC-AUC
        auc_val = compute_roc_auc(y_binary, x)

        kerala_only_rows.append({
            "metric": m,
            "spearman_rho": round(float(rho), 3),
            "ci_low_95": ci_low,
            "ci_high_95": ci_high,
            "p_value": round(float(p), 4),
            "corr_with_slope": round(float(r_xm), 3),
            "partial_rho_controlling_slope": round(float(partial_rho), 3),
            "auc_presence_absence": round(float(auc_val), 3),
            "n_cells": n_kerala
        })

    df_kerala_only = pd.DataFrame(kerala_only_rows)
    csv_kerala_only = out_dir / "studyB_kerala_only.csv"
    df_kerala_only.to_csv(csv_kerala_only, index=False)
    print(f"Saved: {csv_kerala_only}")
    print("\nKerala-Only Centralities vs. Landslide Density Table (n=61 cells):")
    print(df_kerala_only[["metric", "spearman_rho", "ci_low_95", "ci_high_95", "p_value", "partial_rho_controlling_slope", "auc_presence_absence"]])

    # -------------------------------------------------------------------------
    # STEP 4: Study B v2 Ladder (Rainfall, Elevation Controls & Spatial Block Bootstrap)
    # -------------------------------------------------------------------------
    print("\n>>> STEP 4: Study B v2 Ladder with Extra Controls & Spatial-Block Bootstrap")
    
    # Attach 2018 JJAS cumulative rainfall and elevation
    df_kerala = extract_cell_2018_jjas_rainfall(df_kerala, str(imd_rainfall_path))
    df_kerala = extract_cell_elevation(df_kerala)

    # Assign 3x3 grid cells spatial blocks (0.75° x 0.75°)
    block_size_deg = float(config["landslide"].get("spatial_block_size_deg", 0.75))
    df_kerala = assign_spatial_blocks(df_kerala, block_size_deg=block_size_deg)
    n_blocks = df_kerala["block_id"].nunique()
    print(f"Domain partitioned into {n_blocks} spatial blocks ({block_size_deg}° x {block_size_deg}° per block).")

    v2_rows = []
    n_block_boot = int(config["landslide"].get("spatial_block_bootstrap_samples", 1000))

    s_vec = df_kerala["mean_slope"].values
    r_vec = df_kerala["rainfall_2018_jjas"].values
    e_vec = df_kerala["elevation_m"].values

    for m in metrics_list:
        x_vec = df_kerala[m].values
        raw_rho, _ = spearmanr(x_vec, y_dens)
        
        # Stepwise controls ladder
        p_slope = partial_spearman_rank_corr(x_vec, y_dens, [s_vec])
        p_slope_rain = partial_spearman_rank_corr(x_vec, y_dens, [s_vec, r_vec])
        p_all_controls = partial_spearman_rank_corr(x_vec, y_dens, [s_vec, r_vec, e_vec])
        
        # Spatial-block bootstrap CI for full partial correlation
        ci_low, ci_high, se_boot = spatial_block_bootstrap_ci(
            df_kerala,
            metric_col=m,
            target_col="landslide_density",
            control_cols=["mean_slope", "rainfall_2018_jjas", "elevation_m"],
            n_bootstrap=n_block_boot,
            alpha=alpha,
            seed=seed
        )

        auc_val = compute_roc_auc(y_binary, x_vec)

        v2_rows.append({
            "metric": m,
            "raw_spearman_rho": round(float(raw_rho), 3),
            "partial_rho_slope": round(float(p_slope), 3),
            "partial_rho_slope_rain": round(float(p_slope_rain), 3),
            "partial_rho_all_controls": round(float(p_all_controls), 3),
            "block_ci_low_95": ci_low,
            "block_ci_high_95": ci_high,
            "block_bootstrap_se": se_boot,
            "auc_presence_absence": round(float(auc_val), 3),
            "n_cells": n_kerala,
            "n_spatial_blocks": n_blocks
        })

    df_v2 = pd.DataFrame(v2_rows)
    csv_v2 = out_dir / "studyB_v2.csv"
    df_v2.to_csv(csv_v2, index=False)
    print(f"Saved: {csv_v2}")
    print("\nStudy B v2 Full Ladder Table (n=61 Kerala cells, 15 spatial blocks):")
    print(df_v2[["metric", "raw_spearman_rho", "partial_rho_slope", "partial_rho_slope_rain", "partial_rho_all_controls", "block_ci_low_95", "block_ci_high_95", "auc_presence_absence"]])

    print("\n=============================================================")
    print("         Study B Robustness Checks Completed Successfully!    ")
    print("=============================================================\n")


if __name__ == "__main__":
    main()
