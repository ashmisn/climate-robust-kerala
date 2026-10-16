"""
export.py - Serializes and exports all pipeline artifacts to web/public/data/
strictly conforming to the Section 4 Data Contract.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

def compute_config_hash(config: Dict[str, Any]) -> str:
    """Computes short deterministic hash of the configuration dictionary."""
    cfg_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(cfg_str.encode("utf-8")).hexdigest()[:12]

def export_all_contract_data(
    config: Dict[str, Any],
    cells_df: pd.DataFrame,
    links_list: List[Dict[str, Any]],
    basins_impact_df: pd.DataFrame,
    basins_geojson_path: str,
    robustness_results: Dict[str, Any],
    critical_nodes: List[Dict[str, Any]],
    sensitivity_results: Dict[str, Any],
    landslide_stats: Dict[str, Any],
    landslide_points: List[Dict[str, float]],
    output_dir: str = "web/public/data"
) -> None:
    """
    Exports all 9 static contract files to web/public/data/.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    cfg_hash = compute_config_hash(config)
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. meta.json
    meta = {
        "study_area": config.get("study_area", "Kerala (+ Western Ghats buffer)"),
        "period": config.get("period", "1991-2020"),
        "season": config.get("season", "JJAS"),
        "event_percentile": config["events"].get("default_percentile", 95),
        "link_fraction": config["network"].get("link_fraction", 0.05),
        "n_cells": int(len(cells_df)),
        "n_links": int(len(links_list)),
        "generated_at": now_iso,
        "config_hash": cfg_hash
    }
    with open(out / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # 2. cells.geojson
    cell_features = []
    for _, row in cells_df.iterrows():
        coords = json.loads(row["polygon_coords"])
        feat = {
            "type": "Feature",
            "properties": {
                "cell_id": row["cell_id"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "basin_id": row["basin_id"],
                "basin_name": row.get("basin_name", "Other"),
                "mean_slope": float(row.get("mean_slope", 0.0)),
                "max_slope": float(row.get("max_slope", 0.0)),
                "landslide_count_2018": int(row.get("landslide_count_2018", 0)),
                "landslide_density": float(row.get("landslide_density", 0.0)),
                "extreme_days_aug2018": int(row.get("extreme_days_aug2018", 0)),
                "degree": float(row.get("degree", 0.0)),
                "betweenness": float(row.get("betweenness", 0.0)),
                "clustering": float(row.get("clustering", 0.0)),
                "eigenvector": float(row.get("eigenvector", 0.0))
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        }
        cell_features.append(feat)

    cells_geojson = {
        "type": "FeatureCollection",
        "features": cell_features
    }
    with open(out / "cells.geojson", "w", encoding="utf-8") as f:
        json.dump(cells_geojson, f, indent=2)

    # 3. links.json
    with open(out / "links.json", "w", encoding="utf-8") as f:
        json.dump(links_list, f, indent=2)

    # 4. basins.geojson
    # Merge basin geometries with basin impact properties
    impact_lookup = {row["basin_id"]: row for _, row in basins_impact_df.iterrows()}
    basin_features = []
    if Path(basins_geojson_path).exists():
        with open(basins_geojson_path, "r", encoding="utf-8") as f:
            raw_basins = json.load(f)
            for feat in raw_basins.get("features", []):
                bid = feat["properties"]["basin_id"]
                imp = impact_lookup.get(bid, {})
                feat_props = {
                    "basin_id": bid,
                    "name": feat["properties"].get("name", bid),
                    "n_cells": int(imp.get("n_cells", 0)),
                    "impact_rank": int(imp.get("impact_rank", 99)),
                    "lcc_drop_if_removed": float(imp.get("lcc_drop_if_removed", 0.0)),
                    "efficiency_drop_if_removed": float(imp.get("efficiency_drop_if_removed", 0.0))
                }
                feat["properties"] = feat_props
                basin_features.append(feat)

    basins_geojson = {
        "type": "FeatureCollection",
        "features": basin_features
    }
    with open(out / "basins.geojson", "w", encoding="utf-8") as f:
        json.dump(basins_geojson, f, indent=2)

    # 5. robustness.json
    with open(out / "robustness.json", "w", encoding="utf-8") as f:
        json.dump(robustness_results, f, indent=2)

    # 6. critical_nodes.json
    with open(out / "critical_nodes.json", "w", encoding="utf-8") as f:
        json.dump(critical_nodes, f, indent=2)

    # 7. sensitivity.json
    with open(out / "sensitivity.json", "w", encoding="utf-8") as f:
        json.dump(sensitivity_results, f, indent=2)

    # 8. landslide_stats.json
    with open(out / "landslide_stats.json", "w", encoding="utf-8") as f:
        json.dump(landslide_stats, f, indent=2)

    # 9. landslide_points.json (thinned if necessary to keep file small)
    thinned_points = landslide_points[:500] if len(landslide_points) > 500 else landslide_points
    with open(out / "landslide_points.json", "w", encoding="utf-8") as f:
        json.dump(thinned_points, f, indent=2)
