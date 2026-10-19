import numpy as np
import pandas as pd

rain_data = np.load('data/raw/imd_rainfall_real.npz')
cube = rain_data['rainfall']
lats = rain_data['lats']
lons = rain_data['lons']

df_cells = pd.read_parquet('outputs/real_data_run/interim/cells.parquet')
zero_rain_cells = []

for idx, r in df_cells.iterrows():
    cid = r['cell_id']
    lat = r['lat']
    lon = r['lon']
    lat_i = np.argmin(np.abs(lats - lat))
    lon_i = np.argmin(np.abs(lons - lon))
    series = cube[:, lat_i, lon_i]
    total_rain = float(series.sum())
    max_rain = float(series.max())
    if total_rain == 0.0 or max_rain == 0.0:
        zero_rain_cells.append({
            'cell_id': cid,
            'lat': lat,
            'lon': lon,
            'basin_name': r['basin_name'],
            'total_rain': total_rain
        })

print(f"Total zero-rainfall cells found: {len(zero_rain_cells)}")
for c in zero_rain_cells:
    print(f"  - Cell {c['cell_id']}: ({c['lat']}N, {c['lon']}E) in '{c['basin_name']}', total rain = {c['total_rain']} mm")
