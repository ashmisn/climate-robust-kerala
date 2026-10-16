"""
events.py - Extreme precipitation event extraction.
Implements JJAS filtering, wet-day thresholding, percentile calculation,
and continuous inter-annual day indexing.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

def extract_cell_rainfall_series(
    rainfall_cube: np.ndarray,
    lats_all: np.ndarray,
    lons_all: np.ndarray,
    cell_df: pd.DataFrame
) -> np.ndarray:
    """
    Extracts time series matrix (T, N) for all cells in cell_df.
    """
    n_days = rainfall_cube.shape[0]
    n_cells = len(cell_df)
    cell_rain = np.zeros((n_days, n_cells), dtype=np.float32)

    lat_step = lats_all[1] - lats_all[0]
    lon_step = lons_all[1] - lons_all[0]
    lat_origin = lats_all[0]
    lon_origin = lons_all[0]

    for idx, row in cell_df.iterrows():
        lat_idx = int(round((row["lat"] - lat_origin) / lat_step))
        lon_idx = int(round((row["lon"] - lon_origin) / lon_step))
        cell_rain[:, idx] = rainfall_cube[:, lat_idx, lon_idx]

    return cell_rain

def compute_cell_events(
    cell_rain: np.ndarray,
    config: Dict[str, Any],
    years: List[int],
    days_per_year: int = 122
) -> Dict[str, Any]:
    """
    Identifies extreme precipitation days for each cell.
    Uses continuous day index where each year has a 365-day spacing,
    creating a realistic ~243-day non-monsoon winter/spring gap.
    """
    wet_thresh = config["events"].get("wet_day_threshold_mm", 1.0)
    percentiles = config["events"].get("sensitivity_percentiles", [90, 95, 97])
    n_days, n_cells = cell_rain.shape
    n_years = len(years)

    # Build continuous day index array: day_in_season (0..121) + year_idx * 365
    continuous_day_index = np.zeros(n_days, dtype=np.int64)
    august_day_mask = np.zeros(n_days, dtype=bool)

    for y_idx in range(n_years):
        start_t = y_idx * days_per_year
        end_t = start_t + days_per_year
        year_val = years[y_idx]
        
        # In JJAS (June 1 to Sept 30):
        # June: days 0..29 (30 days)
        # July: days 30..60 (31 days)
        # August: days 61..91 (31 days)
        # September: days 92..121 (30 days)
        for d in range(days_per_year):
            t = start_t + d
            continuous_day_index[t] = y_idx * 365 + d
            if year_val == 2018 and (61 <= d <= 91):
                august_day_mask[t] = True

    events_by_pct = {}
    threshold_values_by_pct = {}
    aug2018_extreme_counts = {p: np.zeros(n_cells, dtype=np.int32) for p in percentiles}

    for p in percentiles:
        events_list = []
        thresh_vals = np.zeros(n_cells, dtype=np.float32)

        for c in range(n_cells):
            series = cell_rain[:, c]
            wet_mask = series >= wet_thresh
            if np.sum(wet_mask) > 10:
                p_thresh = np.percentile(series[wet_mask], p)
            else:
                p_thresh = 999.0
            thresh_vals[c] = p_thresh

            # Days exceeding the threshold
            event_mask = series > p_thresh
            event_days = continuous_day_index[event_mask]
            events_list.append(event_days)

            # August 2018 event count
            aug_event_count = np.sum(event_mask & august_day_mask)
            aug2018_extreme_counts[p][c] = aug_event_count

        events_by_pct[p] = events_list
        threshold_values_by_pct[p] = thresh_vals

    return {
        "events_by_pct": events_by_pct,
        "threshold_values_by_pct": threshold_values_by_pct,
        "aug2018_extreme_counts": aug2018_extreme_counts,
        "continuous_day_index": continuous_day_index,
        "cell_rain": cell_rain
    }

def save_events_npz(event_data: Dict[str, Any], output_path: str = "data/interim/events.npz") -> None:
    """Save extracted events to .npz intermediate file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    # Pack event arrays into object dictionary
    save_dict = {
        "thresh_90": event_data["threshold_values_by_pct"][90],
        "thresh_95": event_data["threshold_values_by_pct"][95],
        "thresh_97": event_data["threshold_values_by_pct"][97],
        "aug2018_90": event_data["aug2018_extreme_counts"][90],
        "aug2018_95": event_data["aug2018_extreme_counts"][95],
        "aug2018_97": event_data["aug2018_extreme_counts"][97]
    }
    # Save event arrays per cell for default 95th percentile
    for i, arr in enumerate(event_data["events_by_pct"][95]):
        save_dict[f"events_95_cell_{i}"] = arr
    for i, arr in enumerate(event_data["events_by_pct"][90]):
        save_dict[f"events_90_cell_{i}"] = arr
    for i, arr in enumerate(event_data["events_by_pct"][97]):
        save_dict[f"events_97_cell_{i}"] = arr

    np.savez_compressed(output_path, **save_dict)
