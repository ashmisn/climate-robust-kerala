"""
pipeline/07_landslide_validation.py - Stage 7: Study B Landslide Validation.
Maps 2018 landslide occurrences to cells, joins SRTM DEM slope,
computes overall & slope-stratified Spearman correlations with 1000 bootstrap CIs.
Outputs: data/processed/landslide_stats.parquet
"""

import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ktnet.io import load_config
from src.ktnet.landslide import (
    map_landslides_to_cells,
    attach_dem_slope,
    compute_landslide_correlations
)

def main():
    print("=== Stage 7: Study B Landslide Validation ===")
    config = load_config("config.yaml")

    raw_dir = Path(config["paths"]["raw_data_dir"])
    interim_dir = Path(config["paths"]["interim_data_dir"])
    processed_dir = Path(config["paths"]["processed_data_dir"])

    cells_parquet_path = interim_dir / "cells.parquet"
    metrics_parquet_path = processed_dir / "metrics.parquet"
    events_npz_path = interim_dir / "events.npz"
    landslides_json_path = raw_dir / "landslides_2018.json"
    slope_json_path = raw_dir / "srtm_dem_slope.json"
    out_parquet_path = processed_dir / "landslide_stats.parquet"

    df_cells = pd.read_parquet(cells_parquet_path)
    df_metrics = pd.read_parquet(metrics_parquet_path)
    df_joined = pd.merge(df_cells, df_metrics, on="cell_id")

    # Attach August 2018 extreme precipitation counts
    events_data = np.load(events_npz_path)
    aug_counts_95 = events_data["aug2018_95"]
    df_joined["extreme_days_aug2018"] = aug_counts_95

    # 1. Map landslides
    with open(landslides_json_path, "r", encoding="utf-8") as f:
        landslide_points = json.load(f)
    print(f"Loaded {len(landslide_points)} landslide inventory points.")

    df_joined = map_landslides_to_cells(landslide_points, df_joined, resolution=config["bbox"]["resolution"])
    print(f"Total landslide occurrences mapped inside cells: {df_joined['landslide_count_2018'].sum()}")

    # 2. Attach DEM slope and stratify by tertiles
    with open(slope_json_path, "r", encoding="utf-8") as f:
        dem_slope_data = json.load(f)
    df_joined = attach_dem_slope(df_joined, dem_slope_data)

    # 3. Compute Spearman rank correlations and bootstrap CIs
    n_bootstrap = int(config["landslide"].get("bootstrap_ci_samples", 1000))
    print(f"Computing correlations and {n_bootstrap} bootstrap resamples...")
    stats_dict = compute_landslide_correlations(df_joined, n_bootstrap=n_bootstrap)

    print("Overall Spearman Correlation with Landslide Density:")
    for m, stat in stats_dict["overall"].items():
        print(f"  {m:12s}: rho = {stat['rho']:+.3f} (p = {stat['p']:.4f}, 95% CI: [{stat['ci_low']:+.3f}, {stat['ci_high']:+.3f}])")

    # Save to parquet
    df_joined.to_parquet(out_parquet_path, index=False)
    # Also save the updated cells with all attributes back to interim/cells.parquet
    df_joined.to_parquet(cells_parquet_path, index=False)

    print(f"Stage 7 complete: Saved to {out_parquet_path}")

if __name__ == "__main__":
    main()
