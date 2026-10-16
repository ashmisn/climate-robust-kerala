# Data Provenance Log

This log records the provenance, download date, spatial bounds, and sources for all datasets used in the Kerala Climate Network (Vyuham) research project.

## 1. IMD Gridded Daily Rainfall (0.25° x 0.25°)
- **Source**: India Meteorological Department (IMD), National Climate Centre, Pune.
- **Access Method**: `imdlib` / Open-access IMD daily rainfall archive (1991–2020).
- **Spatial Resolution**: 0.25° x 0.25° (~27 km grid cells).
- **Bounding Box**: Lat 8.0°N – 13.5°N, Lon 74.0°E – 78.0°E (Kerala State + Western Ghats Orographic Buffer).
- **Temporal Coverage**: 1991–2020 (30 years climate standard normal), JJAS (June–September) monsoon focus.
- **Format**: Binary gridded / parquet intermediate (`cells.parquet`, `events.npz`).

## 2. River Basin Boundaries (India-WRIS / CWC)
- **Source**: India Water Resources Information System (India-WRIS) & Central Water Commission (CWC).
- **Basins Identified**:
  - Periyar Basin
  - Bharathapuzha Basin
  - Pamba Basin
  - Chaliyar Basin
  - Chalakudy Basin
  - Kadalundi Basin
  - Muvattupuzha Basin
  - Valapattanam Basin
  - Achankovil Basin
  - Meenachil Basin
  - Ithikkara Basin
  - Kallada Basin
  - Other Coastal / Buffer Basins
- **Attribute Representation**: MultiPolygon GeoJSON coordinates, Basin IDs, and Area.

## 3. Topographic DEM & Slope Data (SRTM 30m)
- **Source**: NASA Shuttle Radar Topography Mission (SRTM) 1 Arc-Second Global DEM (~30m).
- **Derived Metrics**: Zonal mean slope (degrees) and maximum slope (degrees) per 0.25° grid cell.
- **Topographic Classification**: Categorized into slope tertiles (Low, Medium, High).

## 4. 2018 Kerala Landslide Inventory
- **Source**: van Westen, C.J. (2020). "Spatial landslide inventory for Kerala 2018 extreme monsoon disaster".
- **DOI**: [10.17026/dans-x6c-y7x2](https://doi.org/10.17026/dans-x6c-y7x2).
- **Attributes**: Mapped spatial locations (latitude, longitude) of landslides triggered during the catastrophic August 2018 Kerala floods, converted to cell density (count / km²).
