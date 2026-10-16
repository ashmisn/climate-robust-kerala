"""
tests/test_events.py - Unit tests for extreme-event extraction.
Verifies that extreme-event counts per cell are roughly 5% of wet days (sanity check on the 95th percentile).
"""

import numpy as np
import pytest
from src.ktnet.events import compute_cell_events

def test_extreme_event_percentile_sanity():
    np.random.seed(42)
    n_days = 122 * 10
    n_cells = 3
    # Synthetic gamma rainfall
    rain = np.random.gamma(1.5, 10.0, size=(n_days, n_cells)).astype(np.float32)
    # Set 30% days dry (< 1mm)
    rain[rain < 3.0] = 0.5

    config = {
        "events": {
            "wet_day_threshold_mm": 1.0,
            "sensitivity_percentiles": [90, 95, 97]
        }
    }
    years = list(range(1991, 2001))
    res = compute_cell_events(rain, config, years, days_per_year=122)

    for c in range(n_cells):
        wet_count = np.sum(rain[:, c] >= 1.0)
        events_95_count = len(res["events_by_pct"][95][c])
        actual_ratio = events_95_count / wet_count

        # 95th percentile should select approximately 5% of wet days (+/- 2%)
        assert 0.03 <= actual_ratio <= 0.07, f"Expected ~0.05, got {actual_ratio:.3f}"
