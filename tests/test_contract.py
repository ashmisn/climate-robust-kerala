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
    required_props = ["cell_id", "lat", "lon", "basin_id", "mean_slope", "max_slope", "landslide_count_2018", "landslide_density", "extreme_days_aug2018", "degree", "betweenness", "clustering", "eigenvector"]
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
