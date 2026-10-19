# Data Provenance Log

This log records the provenance, download date, spatial bounds, and sources for all datasets used in the Kerala Climate Network (Vyuham) research project.

## Status Summary

| Input Dataset | Current Status | Source / Provenance | File Path |
| :--- | :---: | :--- | :--- |
| **IMD Daily Rainfall (1981–2020)** | **REAL** | India Meteorological Department (IMD) 0.25° gridded daily NetCDF archive (`RF25_ind1981_rfp25.nc` to `RF25_ind2020_rfp25.nc`) | `data/raw/imd_rainfall_real.npz` |
| **Kerala State Boundary** | **REAL** | GADM 4.1 Level-1 administrative boundary (`NAME_1 == "Kerala"`) | `data/raw/kerala_boundary_gadm.geojson` |
| **Kerala District Boundaries** | **REAL** | Census of India 2011 official 14 district polygons | `data/raw/kerala_districts.geojson` |
| **River Basin Boundaries** | **REAL** | Central Water Commission (CWC) / India-WRIS hydrological sub-basins (`WRIS_SubBasin.parquet`) | `data/raw/basins_real.geojson` |
| **SRTM 90m DEM / Terrain Slope** | **REAL** | CGIAR-CSI SRTM 90m v4.1 GeoTIFF tiles (`srtm_51_10`, `srtm_52_10`, `srtm_51_11`, `srtm_52_11`), mosaicked seamlessly across 8.0°–13.5°N, 74.0°–78.0°E (3-arcsecond / 90m resolution) | `data/raw/srtm/` |
| **2018 Landslide Inventory** | **REAL** | Official van Westen (2020) / GSI / NRSC 2018 inventory shapefile (4,728 POINTZ features, WGS84 EPSG:4326) | `data/raw/Kerela landslide.shp` (`.dbf`, `.shx`, `.prj`) |

---

## 1. IMD Gridded Daily Rainfall (0.25° x 0.25°) — REAL
- **Source**: India Meteorological Department (IMD), National Climate Centre, Pune.
- **Acquisition**: Clipped from the official 40-year IMD gridded daily rainfall NetCDF series (1981–2020).
- **Spatial Resolution**: 0.25° x 0.25° (~27.5 km grid cells).
- **Bounding Box**: Lat 8.00°N – 13.50°N (23 latitude intervals), Lon 74.00°E – 78.00°E (17 longitude intervals).
- **Temporal Coverage**: 1981–2020 (40 years climate historical period), JJAS (June 1 – September 30, 122 days/season).
- **Total Frames**: 4,880 daily grids (`rainfall.shape == (4880, 23, 17)`).
- **File**: `data/raw/imd_rainfall_real.npz`.

## 2. Kerala State & District Boundaries — REAL
- **State Boundary**:
  - Source: Database of Global Administrative Areas (GADM) v4.1.
  - Geometry: High-resolution MultiPolygon (2,904 vertices), EPSG:4326.
  - File: `data/raw/kerala_boundary_gadm.geojson`.
- **District Boundaries**:
  - Source: Census of India 2011 / Survey of India.
  - Attributes: All 14 revenue districts (Census codes 588 to 601).
  - File: `data/raw/kerala_districts.geojson`.

## 3. River Basin Boundaries (India-WRIS / CWC) — REAL
- **Source**: India Water Resources Information System (India-WRIS) & Central Water Commission (CWC).
- **Format**: Polygon GeoJSON derived from authoritative `WRIS_SubBasin.parquet`.
- **Identified Hydrological Sub-Basins**:
  1. `Periyar and others` (27 grid cells) — Encompasses Periyar, Muvattupuzha, Chalakudy, Meenachil, Manimala, Achenkovil, Kallada.
  2. `Varrar and others` (17 grid cells) — Encompasses Bharathapuzha (Nila), Chaliyar, Kadalundi, Tirur.
  3. `Netravati and others` (12 grid cells) — Encompasses Valapattanam, Chandragiri, Kuppam, Karyangod.
  4. `Cauvery Upper` (10 grid cells) — Encompasses Kabini (Wayanad).
  5. `Cauvery Middle` (10 grid cells) — Encompasses Bhavani (Silent Valley/Palakkad) and Pambar (Idukki).
  6. `Pamba and others` / `Vaippar and others` (2 grid cells) — Eastern Ghats passes.
- **File**: `data/raw/basins_real.geojson`.

## 4. Topographic DEM & Slope Data — REAL
- **Status**: **REAL** (Acquired and processed).
- **Source**: CGIAR Consortium for Spatial Information (CGIAR-CSI) SRTM 90m Digital Elevation Database v4.1 (NASA Shuttle Radar Topography Mission, post-processed void-filled).
- **Downloaded Tiles**:
  - `srtm_51_10.tif` (Lat 5°–10°N, Lon 70°–75°E)
  - `srtm_52_10.tif` (Lat 5°–10°N, Lon 75°–80°E)
  - `srtm_51_11.tif` (Lat 10°–15°N, Lon 70°–75°E)
  - `srtm_52_11.tif` (Lat 10°–15°N, Lon 75°–80°E)
- **Directory**: `data/raw/srtm/`
- **Mosaic Resolution**: $12,000 \times 12,000$ pixels at 3-arcsecond spacing (~90 m).
- **Gradients**: Meter-scaled physical gradients in degrees computed per pixel via central finite differences accounting for latitude-dependent longitude scaling.
- **Derived Cell Metrics**: `slope_dem_mean`, `slope_dem_p90`, `frac_pixels_over_25deg`, `elev_mean`. Zero circularity or leakage.

## 5. 2018 Kerala Landslide Inventory — REAL
- **Source**: van Westen, C.J. (2020) dataset (*"Spatial landslide inventory for Kerala 2018 extreme monsoon disaster"*, DANS DOI: 10.17026/dans-x6c-y7x2) compiled with Geological Survey of India (GSI) & National Remote Sensing Centre (NRSC).
- **Files**: `data/raw/Kerela landslide.shp`, `Kerela landslide.dbf`, `Kerela landslide.shx`, `Kerela landslide.prj`, `Kerela landslide.cpg`, `Kerela landslide.sbn`.
- **Feature Count**: Exactly 4,728 records.
- **Geometry Type**: `POINTZ` (Initiation/occurrence point coordinates with elevation $Z$).
- **Coordinate Reference System (CRS)**: `GEOGCS["GCS_WGS_1984", EPSG:4326]`.
- **Bounding Box**: Lat $8.4745^\circ\text{N}$ – $12.6550^\circ\text{N}$, Lon $75.0154^\circ\text{E}$ – $77.3963^\circ\text{E}$.
- **Core Attributes**: `No`, `District`, `NRSC`, `GSI`, `New`, `Type_of_sl`, `Length`, `Width`, `Area`, `Building_I`, `Road_impac`, `Impact_Agr`, `LU_2010`, `LU_2018`, `Specific_r`, `Remarks`, `POINT_X`, `POINT_Y`, `Reclass_Sl`, `RASTERVALU`.

---

## 6. Formal Academic Citations for Datasets & Methodology

### 6.1 Observational Datasets
1. **IMD Gridded Daily Rainfall Dataset**:
   * Pai, D. S., Sridhar, L., Rajeevan, M., Kshirsagar, M., Mehrotra, R., & Sankar, S. (2014). Development of a new high spatial resolution ($0.25^\circ \times 0.25^\circ$) long period (1901–2010) daily gridded rainfall data set over India and its comparison with existing data sets. *MAUSAM*, 65(1), 1–18. https://doi.org/10.54302/mausam.v65i1.851
   * Rajeevan, M., Bhate, J., & Jaswal, A. K. (2008). Analysis of variability and trends of extreme rainfall events over India using 104 years of gridded daily rainfall data. *Geophysical Research Letters*, 35(18), L18707. https://doi.org/10.1029/2008GL035143

2. **2018 Kerala Landslide Inventory**:
   * van Westen, C. J., Martha, T. R., & Kuriakose, S. L. (2020). *Spatial landslide inventory for Kerala 2018 extreme monsoon disaster*. DANS Data Station Physical and Technical Sciences. https://doi.org/10.17026/dans-x6c-y7x2
   * Geological Survey of India (GSI) & National Remote Sensing Centre (NRSC), ISRO (2018). *Comprehensive Report on the Catastrophic Landslides in Kerala during August 2018 Monsoon Disaster*. Ministry of Mines & Department of Space, Government of India.

3. **CGIAR-CSI SRTM 90m Digital Elevation Model v4.1**:
   * Jarvis, A., Reuter, H. I., Nelson, A., & Guevara, E. (2008). *Hole-filled seamless SRTM data V4*. International Centre for Tropical Agriculture (CIAT). http://srtm.csi.cgiar.org
   * Farr, T. G., Rosen, P. A., Caro, E., Crippen, R., Duren, R., Hensley, S., Kobrick, M., Paller, M., Rodriguez, E., Roth, L., Seal, D., Shaffer, S., Shimada, J., Umland, J., Werner, M., Oskin, M., Burbank, D., & Alsdorf, D. (2007). The Shuttle Radar Topography Mission. *Reviews of Geophysics*, 45(2), RG2004. https://doi.org/10.1029/2005RG000183

4. **India-WRIS / CWC River Basins**:
   * Central Water Commission (CWC) & National Remote Sensing Centre (NRSC) (2014). *Watershed Atlas of India*. Ministry of Water Resources, River Development and Ganga Rejuvenation, Government of India, New Delhi.
   * India Water Resources Information System (India-WRIS) (2020). *Hydrological Sub-Basin Database of India*. Ministry of Jal Shakti, Government of India. https://indiawris.gov.in

5. **Administrative Boundaries (GADM & Census)**:
   * Global Administrative Areas (2022). *GADM database of Global Administrative Areas, version 4.1*. University of California, Berkeley. https://gadm.org
   * Office of the Registrar General & Census Commissioner, India (2011). *Census of India 2011: Administrative Atlas of India*. Ministry of Home Affairs, Government of India, New Delhi.

### 6.2 Complex Network & Event Synchronization Methodology
1. **Event Synchronization Formulation**:
   * Quiroga, R. Q., Kreuz, T., & Grassberger, P. (2002). Event synchronization: a simple and fast method to measure synchronicity and time delay between event series. *Physical Review E*, 66(4), 041904. https://doi.org/10.1103/PhysRevE.66.041904
   * Boers, N., Bookhagen, B., Barbosa, H. M., Marwan, N., Kurths, J., & Marengo, J. A. (2014). Prediction of extreme rainfall in South America by complex networks. *Nature Communications*, 5(1), 5199. https://doi.org/10.1038/ncomms6199
   * Malik, N., Bookhagen, B., Marwan, N., & Kurths, J. (2012). Analysis of spatial and temporal extreme rainfall patterns in the South Asian monsoon region using complex networks. *Climate Dynamics*, 39(3), 971–987. https://doi.org/10.1007/s00382-011-1156-4

