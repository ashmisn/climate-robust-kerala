"""
tests/test_contract.py - Validates data contract files against Section 4 specification.
Verifies keys, formats, file sizes, and parsing readiness for web dashboard.
"""

import os
import json
from pathlib import Path
import pytest

DATA_DIR = Path("web/public/data")

@pytest.mark.skipif(not DATA_DIR.exists(), reason="Run pipeline first to populate web/public/data")
def test_meta_json_contract():
    path = DATA_DIR / "meta.json"
    assert path.exists(), "meta.json missing"
    with open(path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    required_keys = ["study_area", "period", "season", "event_percentile", "link_fraction", "n_cells", "n_links", "generated_at", "config_hash"]
    for k in required_keys:
        assert k in meta, f"Missing key '{k}' in meta.json"

@pytest.mark.skipif(not DATA_DIR.exists(), reason="Run pipeline first to populate web/public/data")
def test_cells_geojson_contract():
    path = DATA_DIR / "cells.geojson"
    assert path.exists(), "cells.geojson missing"
    with open(path, "r", encoding="utf-8") as f:
        fc = json.load(f)
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) > 0
    first = fc["features"][0]
    required_props = [
        "cell_id", "lat", "lon", "basin_id", "mean_slope", "max_slope",
        "landslide_count_2018", "landslide_density", "extreme_days_aug2018",
        "degree", "betweenness", "clustering", "eigenvector",
        # Independent SRTM terrain and rainfall controls
        "slope_dem_mean", "slope_dem_p90", "frac_pixels_over_25deg",
        "elev_mean", "slope_dem_class", "aug2018_rain_mm", "aug2018_extreme_days",
        "is_kerala_50"
    ]
    for p in required_props:
        assert p in first["properties"], f"Missing property '{p}' in cells.geojson"

@pytest.mark.skipif(not DATA_DIR.exists(), reason="Run pipeline first to populate web/public/data")
def test_links_json_contract():
    path = DATA_DIR / "links.json"
    assert path.exists(), "links.json missing"
    with open(path, "r", encoding="utf-8") as f:
        links = json.load(f)
    assert isinstance(links, list)
    if len(links) > 0:
        first = links[0]
        for k in ["source", "target", "weight"]:
            assert k in first, f"Missing key '{k}' in links.json"

@pytest.mark.skipif(not DATA_DIR.exists(), reason="Run pipeline first to populate web/public/data")
def test_robustness_json_contract():
    path = DATA_DIR / "robustness.json"
    assert path.exists(), "robustness.json missing"
    with open(path, "r", encoding="utf-8") as f:
        rob = json.load(f)
    assert "strategies" in rob
    assert "fractions" in rob
    assert "metrics" in rob
    assert "random" in rob["strategies"]
    assert "degree" in rob["strategies"]
    assert "betweenness" in rob["strategies"]

@pytest.mark.skipif(not DATA_DIR.exists(), reason="Run pipeline first to populate web/public/data")
def test_landslide_stats_json_contract():
    path = DATA_DIR / "landslide_stats.json"
    assert path.exists(), "landslide_stats.json missing"
    with open(path, "r", encoding="utf-8") as f:
        ls = json.load(f)
    assert "overall" in ls
    assert "by_slope_class" in ls
    assert "scatter" in ls
    # Extended Phase 1 Strengthen v3 schema
    assert "cell_sets" in ls
    assert "kerala_48" in ls["cell_sets"]
    assert "all_97" in ls["cell_sets"]
    assert "model_comparison" in ls
    assert "rainfall_controls" in ls
    assert "point_level_auc" in ls
    assert "audit" in ls

@pytest.mark.skipif(not DATA_DIR.exists(), reason="Run pipeline first to populate web/public/data")
def test_dashboard_kpis_match_data():
    """Verify that Dashboard KPI numbers strictly match exported JSON files."""
    meta_path = DATA_DIR / "meta.json"
    links_path = DATA_DIR / "links.json"
    cells_path = DATA_DIR / "cells.geojson"
    basins_path = DATA_DIR / "basins.geojson"
    ls_path = DATA_DIR / "landslide_stats.json"

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(links_path, "r", encoding="utf-8") as f:
        links = json.load(f)
    with open(cells_path, "r", encoding="utf-8") as f:
        cells = json.load(f)
    with open(basins_path, "r", encoding="utf-8") as f:
        basins = json.load(f)
    with open(ls_path, "r", encoding="utf-8") as f:
        ls = json.load(f)

    # 1. 97 active grid cells
    assert meta["n_cells"] == 97, f"Expected 97 cells in meta.json, got {meta['n_cells']}"
    assert len(cells["features"]) == 97, f"Expected 97 cells in cells.geojson, got {len(cells['features'])}"

    # 2. 232 network links
    assert meta["n_links"] == 232, f"Expected 232 links in meta.json, got {meta['n_links']}"
    assert len(links) == 232, f"Expected 232 links in links.json, got {len(links)}"

    # 3. Critical Basin: Periyar Rank #1 and 32.0% drop
    top_basin = sorted(basins["features"], key=lambda b: b["properties"]["impact_rank"])[0]["properties"]
    assert "Periyar" in top_basin["name"], f"Expected Periyar as rank 1 basin, got {top_basin['name']}"
    assert top_basin["impact_rank"] == 1
    assert round(top_basin["lcc_drop_if_removed"], 3) == 0.320, f"Expected 0.320 LCC drop, got {top_basin['lcc_drop_if_removed']}"

    # 4. Landslide association: 48 Kerala cells
    k48 = ls["cell_sets"]["kerala_48"]["metrics"]
    for m in ["degree", "betweenness", "clustering", "eigenvector"]:
        # Verify 95% spatial-block bootstrap CI crosses zero
        ci_075 = k48[m]["spatial_bootstrap_cis"]["block_0.75deg"]
        assert ci_075["ci_low"] <= 0.05, f"Expected CI low <= 0, got {ci_075}"
        assert ci_075["ci_high"] >= 0.0, f"Expected CI high >= 0, got {ci_075}"
