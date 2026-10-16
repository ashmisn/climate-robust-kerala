"""
pipeline/02_build_grid.py - Stage 2: Grid and Basin Spatial Assignment.
Builds 0.25° grid over bbox, drops ocean cells, assigns cells to river basins.
Outputs: data/interim/cells.parquet
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ktnet.io import load_config
from src.ktnet.grid import build_cell_grid, save_cells_parquet

def main():
    print("=== Stage 2: Grid Construction & Basin Assignment ===")
    config = load_config("config.yaml")

    basins_path = str(Path(config["paths"]["raw_data_dir"]) / "basins.geojson")
    out_cells_path = str(Path(config["paths"]["interim_data_dir"]) / "cells.parquet")

    df_cells = build_cell_grid(config, basins_geojson_path=basins_path)
    print(f"Generated {len(df_cells)} land cells covering Kerala and Western Ghats buffer.")
    print(f"Basin distribution:\n{df_cells['basin_name'].value_counts()}")

    save_cells_parquet(df_cells, out_cells_path)
    print(f"Stage 2 complete: Saved to {out_cells_path}")

if __name__ == "__main__":
    main()
