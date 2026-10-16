"""
pipeline/03_extract_events.py - Stage 3: Extreme Precipitation Event Extraction.
Extracts wet-day (>= 1mm) rainfall, computes 90/95/97 percentile thresholds,
and generates continuous day indices across 1991-2020.
Outputs: data/interim/events.npz
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ktnet.io import load_config
from src.ktnet.events import extract_cell_rainfall_series, compute_cell_events, save_events_npz

def main():
    print("=== Stage 3: Extreme Event Extraction ===")
    config = load_config("config.yaml")

    raw_rain_path = Path(config["paths"]["raw_data_dir"]) / "imd_rainfall.npz"
    cells_parquet_path = Path(config["paths"]["interim_data_dir"]) / "cells.parquet"
    out_events_path = Path(config["paths"]["interim_data_dir"]) / "events.npz"

    rain_data = np.load(raw_rain_path)
    rainfall_cube = rain_data["rainfall"]
    lats = rain_data["lats"]
    lons = rain_data["lons"]
    years = rain_data["years"].tolist()
    days_per_year = int(rain_data["days_per_year"])

    df_cells = pd.read_parquet(cells_parquet_path)
    print(f"Extracting rainfall for {len(df_cells)} cells over {len(years)} JJAS monsoon seasons...")

    cell_rain = extract_cell_rainfall_series(rainfall_cube, lats, lons, df_cells)
    event_data = compute_cell_events(cell_rain, config, years, days_per_year)

    for p in [90, 95, 97]:
        total_events = sum(len(arr) for arr in event_data["events_by_pct"][p])
        avg_events = total_events / len(df_cells)
        print(f"Threshold {p}th percentile: total {total_events} events, avg {avg_events:.1f} events/cell.")

    save_events_npz(event_data, str(out_events_path))
    print(f"Stage 3 complete: Saved to {out_events_path}")

if __name__ == "__main__":
    main()
