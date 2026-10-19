"""
tests/test_landslide_controls.py - Unit tests for Study B controls, boundary tagging, and spatial block bootstrap.
"""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from src.ktnet.landslide_controls import (
    tag_kerala_cells,
    assign_spatial_blocks,
    partial_spearman_rank_corr,
    compute_roc_auc,
    spatial_block_bootstrap_ci
)


def test_tag_kerala_cells():
    df_toy = pd.DataFrame({
        "cell_id": ["c1", "c2"],
        "lat": [9.5, 9.5],
        "lon": [76.5, 77.8]  # c1 inside Kerala, c2 in eastern Tamil Nadu buffer
    })
    tagged = tag_kerala_cells(df_toy)
    assert "inside_kerala" in tagged.columns
    assert tagged.loc[0, "inside_kerala"] is True or tagged.loc[0, "inside_kerala"] == True
    assert tagged.loc[1, "inside_kerala"] is False or tagged.loc[1, "inside_kerala"] == False


def test_assign_spatial_blocks():
    df_toy = pd.DataFrame({
        "cell_id": ["c1", "c2", "c3"],
        "lat": [9.0, 9.2, 10.5],
        "lon": [76.0, 76.2, 76.0]
    })
    blocked = assign_spatial_blocks(df_toy, block_size_deg=0.75)
    assert "block_id" in blocked.columns
    # c1 and c2 are in same 0.75x0.75 block
    assert blocked.loc[0, "block_id"] == blocked.loc[1, "block_id"]
    # c3 is in a different latitude block
    assert blocked.loc[0, "block_id"] != blocked.loc[2, "block_id"]


def test_partial_spearman_rank_corr():
    np.random.seed(42)
    n = 50
    z = np.linspace(0, 10, n)
    x = 0.8 * z + np.random.normal(0, 1, n)
    y = 0.8 * z + np.random.normal(0, 1, n)
    
    # Raw correlation should be high due to confounding by z
    raw_r, _ = spearmanr(x, y)
    assert raw_r > 0.4
    
    # Partial correlation controlling for z
    p_r = partial_spearman_rank_corr(x, y, [z])
    assert -0.3 < p_r < 0.3  # Z accounts for the spurious correlation


def test_compute_roc_auc():
    y_true = np.array([0, 0, 1, 1])
    y_score = np.array([0.1, 0.4, 0.6, 0.9])
    auc = compute_roc_auc(y_true, y_score)
    assert auc == 1.0


def test_spatial_block_bootstrap_ci():
    np.random.seed(42)
    df_toy = pd.DataFrame({
        "block_id": ["b1", "b1", "b2", "b2", "b3", "b3"] * 5,
        "metric": np.random.normal(0, 1, 30),
        "target": np.random.normal(0, 1, 30),
        "control1": np.random.normal(0, 1, 30)
    })
    ci_low, ci_high, se = spatial_block_bootstrap_ci(
        df_toy,
        metric_col="metric",
        target_col="target",
        control_cols=["control1"],
        n_bootstrap=100,
        seed=42
    )
    assert ci_low <= ci_high
    assert se >= 0.0


def test_geometry_to_cell_counting_toy():
    """Verifies point and polygon centroid mapping onto toy grid cells."""
    from src.ktnet.landslide import map_landslides_to_cells

    cells_toy = pd.DataFrame({
        "cell_id": ["c1", "c2"],
        "lat": [10.0, 10.0],
        "lon": [76.0, 76.25],
        "area_km2": [700.0, 700.0]
    })
    # 3 points falling in c1 bounding box, 1 in c2, 1 outside domain
    points = [
        {"lat": 10.05, "lon": 76.02},  # c1
        {"lat": 9.98, "lon": 75.95},   # c1
        {"lat": 10.00, "lon": 76.00},  # c1
        {"lat": 10.02, "lon": 76.24},  # c2
        {"lat": 12.50, "lon": 77.00},  # outside
    ]
    res = map_landslides_to_cells(points, cells_toy, resolution=0.25)
    assert res.loc[res["cell_id"] == "c1", "landslide_count_2018"].iloc[0] == 3
    assert res.loc[res["cell_id"] == "c2", "landslide_count_2018"].iloc[0] == 1
    assert np.isclose(res.loc[res["cell_id"] == "c1", "landslide_density"].iloc[0], round(3 / 700.0, 5))
    assert np.isclose(res.loc[res["cell_id"] == "c2", "landslide_density"].iloc[0], round(1 / 700.0, 5))


def test_pending_fallback():
    """Verifies that pending state json structure and complete state comply with contract without errors."""
    import json
    from pathlib import Path

    # 1. Verify toy pending fallback object structure
    toy_pending = {
        "status": "pending",
        "message": "Pending real inventory and DEM",
        "overall": {"degree": {"rho": 0.0, "p": 1.0, "ci_low": 0.0, "ci_high": 0.0}},
        "by_slope_class": [],
        "scatter": []
    }
    assert toy_pending.get("status") == "pending"
    assert "Pending" in toy_pending.get("message")
    assert isinstance(toy_pending.get("overall"), dict)
    assert len(toy_pending.get("scatter")) == 0

    # 2. Verify live landslide_stats.json adheres to schema
    path = Path("web/public/data/landslide_stats.json")
    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("status") in ["pending", "complete"]
    assert isinstance(data.get("overall"), dict)
    assert isinstance(data.get("scatter"), list)
    assert isinstance(data.get("by_slope_class"), list)
    assert "degree" in data["overall"]


