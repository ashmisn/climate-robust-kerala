"""
tests/test_phase1_strengthen.py - Unit tests for Phase 1 strengthening functions.
Tests permutation test bounds, seed reproducibility, multi-scale bootstrap, CV, and date identification.
"""

import numpy as np
import pandas as pd
import pytest
from src.ktnet.phase1_strengthen import (
    permutation_test_partial_spearman,
    spatial_block_bootstrap_multiscale,
    leave_one_block_cv,
    extract_august_2018_cumulative_rainfall
)


def test_permutation_test_bounds_and_reproducibility():
    np.random.seed(42)
    n = 40
    z = np.random.uniform(0, 10, n)
    x = 0.5 * z + np.random.normal(0, 1, n)
    y = 0.5 * z + np.random.normal(0, 1, n)

    rho1, p1 = permutation_test_partial_spearman(x, y, [z], n_permutations=500, seed=42)
    rho2, p2 = permutation_test_partial_spearman(x, y, [z], n_permutations=500, seed=42)

    # Deterministic with same seed
    assert rho1 == rho2
    assert p1 == p2
    # Probability bounds
    assert 0.0 <= p1 <= 1.0
    assert -1.0 <= rho1 <= 1.0


def test_spatial_block_bootstrap_multiscale():
    np.random.seed(42)
    df_toy = pd.DataFrame({
        "lat": np.linspace(8.5, 12.0, 30),
        "lon": np.linspace(75.0, 77.0, 30),
        "metric": np.random.normal(0, 1, 30),
        "density": np.random.uniform(0, 2, 30),
        "mean_slope": np.random.uniform(5, 30, 30)
    })

    res = spatial_block_bootstrap_multiscale(
        df_toy,
        metric_col="metric",
        target_col="density",
        control_cols=["mean_slope"],
        block_sizes=[0.5, 1.0],
        n_bootstrap=100,
        seed=42
    )

    assert "block_0.50deg" in res
    assert "block_1.00deg" in res
    for b_key in res:
        b_res = res[b_key]
        assert b_res["ci_low"] <= b_res["ci_high"]
        assert b_res["n_blocks"] > 0
        assert b_res["se"] >= 0.0


def test_leave_one_block_cv():
    np.random.seed(42)
    df_toy = pd.DataFrame({
        "lat": np.repeat(np.linspace(8.5, 11.5, 6), 5),
        "lon": np.tile(np.linspace(75.5, 77.0, 5), 6),
        "mean_slope": np.random.uniform(2, 35, 30),
        "degree": np.random.uniform(2, 20, 30),
        "betweenness": np.random.uniform(0, 0.1, 30),
        "clustering": np.random.uniform(0, 0.5, 30),
        "eigenvector": np.random.uniform(0, 0.3, 30),
        "landslide_density": np.random.uniform(0, 1.5, 30),
        "landslide_count_2018": np.random.choice([0, 1, 5, 20], size=30, p=[0.4, 0.3, 0.2, 0.1])
    })

    cv_res = leave_one_block_cv(df_toy, block_sizes=[0.75], seed=42)
    assert "block_0.75deg" in cv_res
    info = cv_res["block_0.75deg"]
    assert "r2_null" in info
    assert "r2_slope_only" in info
    assert "r2_slope_plus_metrics" in info
    assert "auc_null" in info
    assert 0.0 <= info["auc_slope_only"] <= 1.0


def test_extract_august_2018_cumulative_rainfall(tmp_path):
    # Create toy NPZ archive with known values
    years = np.array([2017, 2018], dtype=int)
    days_per_year = 122
    lats = np.array([10.0, 10.25])
    lons = np.array([76.0, 76.25])
    
    # 2 years * 122 days = 244 days
    cube = np.zeros((244, 2, 2), dtype=np.float32)
    # August 2018 is index: year 1 * 122 + 61 to 91 inclusive
    aug_start = 122 + 61
    aug_end = 122 + 92
    cube[aug_start:aug_end, 0, 0] = 10.0  # 31 days * 10 = 310.0 mm
    
    test_npz = tmp_path / "toy_rain.npz"
    np.savez(test_npz, rainfall=cube, years=years, days_per_year=days_per_year, lats=lats, lons=lons)
    
    cells_toy = pd.DataFrame({
        "cell_id": ["c1"],
        "lat": [10.0],
        "lon": [76.0]
    })
    
    rain_series = extract_august_2018_cumulative_rainfall(str(test_npz), cells_toy)
    assert len(rain_series) == 1
    assert np.isclose(rain_series.iloc[0], 310.0)
