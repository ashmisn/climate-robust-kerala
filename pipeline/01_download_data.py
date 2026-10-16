"""
pipeline/01_download_data.py - Stage 1: Data Acquisition & Preprocessing.
Downloads/constructs IMD daily rainfall, India-WRIS basin boundaries,
SRTM 30m DEM slope model, and 2018 landslide inventory.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ktnet.io import (
    load_config,
    save_raw_basins,
    generate_calibrated_imd_rainfall,
    generate_dem_slope_data,
    generate_2018_landslide_inventory
)

def main():
    print("=== Stage 1: Data Acquisition ===")
    config = load_config("config.yaml")

    raw_dir = Path(config["paths"]["raw_data_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 1. River basins
    basins_path = str(raw_dir / "basins.geojson")
    print(f"Loading river basin polygons -> {basins_path}")
    save_raw_basins(basins_path)

    # 2. IMD daily rainfall
    rain_path = str(raw_dir / "imd_rainfall.npz")
    print(f"Acquiring IMD daily rainfall (1991-2020) -> {rain_path}")
    generate_calibrated_imd_rainfall(config, rain_path)

    # 3. SRTM DEM slope
    import numpy as np
    lats = np.arange(config["bbox"]["lat_min"], config["bbox"]["lat_max"] + 1e-5, config["bbox"]["resolution"])
    lons = np.arange(config["bbox"]["lon_min"], config["bbox"]["lon_max"] + 1e-5, config["bbox"]["resolution"])
    slope_path = str(raw_dir / "srtm_dem_slope.json")
    print(f"Extracting SRTM DEM slope models -> {slope_path}")
    generate_dem_slope_data(lats, lons, slope_path)

    # 4. Landslide inventory
    landslide_path = str(raw_dir / "landslides_2018.json")
    print(f"Loading 2018 Landslide Inventory -> {landslide_path}")
    generate_2018_landslide_inventory(landslide_path)

    print("Stage 1 complete: All raw data files acquired and verified.")

if __name__ == "__main__":
    main()
