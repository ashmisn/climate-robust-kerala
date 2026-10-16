"""
grid.py - 0.25° grid construction, land cell filtering, and basin spatial assignment.
Builds the fundamental cell table (cells.parquet) per Stage 2 scientific spec.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon, shape

def is_land_cell(lat: float, lon: float) -> bool:
    """
    Filters land cells covering Kerala and Western Ghats buffer zone.
    Drops open ocean cells in the Arabian Sea and distant interior Deccan plateau.
    """
    # Coastline western boundary interpolation from South to North
    # 8.0°N: lon >= 76.8°E
    # 9.0°N: lon >= 76.3°E
    # 10.0°N: lon >= 75.9°E
    # 11.0°N: lon >= 75.5°E
    # 12.0°N: lon >= 74.9°E
    # 13.0°N: lon >= 74.6°E
    coast_lon = 76.8 - 0.44 * (lat - 8.0)
    # Eastern Western Ghats buffer boundary (~77.4°E at 8.5°N, ~76.2°E at 12.8°N)
    east_lon = 77.45 - 0.24 * (lat - 8.0)

    if lat < 8.2 or lat > 12.9:
        return False

    return (lon >= (coast_lon - 0.05)) and (lon <= (east_lon + 0.15))

def build_cell_grid(config: Dict[str, Any], basins_geojson_path: str = "data/raw/basins.geojson") -> pd.DataFrame:
    """
    Constructs 0.25° cells across the bounding box, assigns cells to basins,
    and returns a pandas DataFrame.
    """
    lat_min = config["bbox"]["lat_min"]
    lat_max = config["bbox"]["lat_max"]
    lon_min = config["bbox"]["lon_min"]
    lon_max = config["bbox"]["lon_max"]
    res = config["bbox"]["resolution"]
    area_km2 = config["grid"].get("approx_cell_area_km2", 756.25)

    # Load basin polygons
    basin_polygons = []
    if Path(basins_geojson_path).exists():
        with open(basins_geojson_path, "r", encoding="utf-8") as f:
            b_data = json.load(f)
            for feat in b_data.get("features", []):
                poly = shape(feat["geometry"])
                basin_polygons.append({
                    "basin_id": feat["properties"]["basin_id"],
                    "name": feat["properties"].get("name", feat["properties"]["basin_id"]),
                    "geom": poly
                })

    lats = np.arange(lat_min, lat_max + 1e-5, res)
    lons = np.arange(lon_min, lon_max + 1e-5, res)

    cells = []
    cell_counter = 1

    for lat in lats:
        for lon in lons:
            lat = round(float(lat), 2)
            lon = round(float(lon), 2)
            if not is_land_cell(lat, lon):
                continue

            pt = Point(lon, lat)
            assigned_basin_id = "other"
            assigned_basin_name = "Other / Coastal Buffer"

            for b in basin_polygons:
                if b["geom"].contains(pt):
                    assigned_basin_id = b["basin_id"]
                    assigned_basin_name = b["name"]
                    break

            cell_id = f"c_{cell_counter:03d}"
            cell_counter += 1

            half_res = res / 2.0
            poly_coords = [
                [round(lon - half_res, 4), round(lat - half_res, 4)],
                [round(lon + half_res, 4), round(lat - half_res, 4)],
                [round(lon + half_res, 4), round(lat + half_res, 4)],
                [round(lon - half_res, 4), round(lat + half_res, 4)],
                [round(lon - half_res, 4), round(lat - half_res, 4)]
            ]

            cells.append({
                "cell_id": cell_id,
                "lat": lat,
                "lon": lon,
                "area_km2": area_km2,
                "basin_id": assigned_basin_id,
                "basin_name": assigned_basin_name,
                "polygon_coords": json.dumps(poly_coords)
            })

    df = pd.DataFrame(cells)
    return df

def save_cells_parquet(df: pd.DataFrame, output_path: str = "data/interim/cells.parquet") -> None:
    """Save grid DataFrame to parquet."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
