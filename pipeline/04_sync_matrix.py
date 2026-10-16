"""
pipeline/04_sync_matrix.py - Stage 4: Event Synchronization (Quiroga et al. 2002).
Computes dynamic lag, symmetric normalized score Q_ij using numba.
Outputs: data/interim/es_matrix.npy
"""

import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ktnet.io import load_config
from src.ktnet.sync import compute_full_es_matrix

def main():
    print("=== Stage 4: Event Synchronization Matrix ===")
    config = load_config("config.yaml")

    events_npz_path = Path(config["paths"]["interim_data_dir"]) / "events.npz"
    cells_parquet_path = Path(config["paths"]["interim_data_dir"]) / "cells.parquet"
    out_es_path = Path(config["paths"]["interim_data_dir"]) / "es_matrix.npy"

    df_cells = pd.read_parquet(cells_parquet_path)
    n_cells = len(df_cells)

    events_data = np.load(events_npz_path)
    # Default 95th percentile events
    event_series_list = [events_data[f"events_95_cell_{i}"] for i in range(n_cells)]

    max_lag = float(config["sync"].get("max_lag_days", 10.0))
    print(f"Computing {n_cells}x{n_cells} Event Synchronization matrix (max lag = {max_lag} days)...")

    start_time = time.time()
    es_matrix = compute_full_es_matrix(event_series_list, max_lag=max_lag)
    elapsed = time.time() - start_time

    print(f"Computed in {elapsed:.3f} seconds.")
    print(f"ES Matrix shape: {es_matrix.shape}, Min: {es_matrix.min():.4f}, Max: {es_matrix.max():.4f}, Mean: {es_matrix.mean():.4f}")

    # Check symmetry
    sym_diff = np.max(np.abs(es_matrix - es_matrix.T))
    print(f"Symmetry max absolute difference: {sym_diff:.8f}")

    np.save(out_es_path, es_matrix)
    print(f"Stage 4 complete: Saved to {out_es_path}")

if __name__ == "__main__":
    main()
