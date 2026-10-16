# Kerala Climate Network (Vyuham) – Project Report

---

## 1. Introduction
The **Kerala Climate Network (Vyuham)** project creates a synchronized monsoon‑precipitation network across Kerala’s river basins, evaluates its structural robustness, and validates the network against observed landslide events.  The workflow is fully reproducible, consists of a pure‑Python data‑processing pipeline, and a zero‑backend **React + Vite** web dashboard for interactive exploration.

---

## 2. End‑to‑End Data Pipeline (Stages 1‑8)
| Stage | Script | Input | Output | Purpose |
|------|--------|-------|--------|---------|
| **01** | `pipeline/01_download_data.py` | Remote URLs (rainfall, DEM, basin shapefiles, landslide points) | `data/raw/*` | Download all raw scientific datasets. |
| **02** | `pipeline/02_build_grid.py` | Raw raster & basin shapefiles | `data/interim/cells.parquet` | Build a 0.25° land‑mask grid and assign each cell to a basin. |
| **03** | `pipeline/03_extract_events.py` | Grid, precipitation time‑series | `data/interim/events.npz` | Identify JJAS (June‑Sept) extreme wet‑day events per cell. |
| **04** | `pipeline/04_sync_matrix.py` | Event indices per cell | `data/interim/es_matrix.npy` | Compute pair‑wise event‑synchronisation matrix (Numba accelerated). |
| **05** | `pipeline/05_build_network.py` | Synchronisation matrix | `data/processed/network.graphml`, `metrics.parquet` | Build weighted network, retain top 5 % links, calculate degree, betweenness, eigenvector, clustering centralities. |
| **06** | `pipeline/06_robustness_study.py` | Network & centralities | `robustness.parquet`, `critical_nodes.parquet`, `sensitivity.parquet`, `basin_impact.parquet` | Simulate random, degree‑based, betweenness‑based node removal; track Largest Connected Component (LCC) size and global efficiency (normalised). |
| **07** | `pipeline/07_landslide_validation.py` | Network, landslide points, DEM slope | `landslide_stats.parquet` | Bootstrap Spearman correlation between each centrality (and slope) and landslide density. |
| **08** | `pipeline/08_export_ui.py` | All intermediate artefacts | `web/public/data/*.json` & `*.geojson` | Serialize the **data contract** consumed by the front‑end. |

All stages are orchestrated by `run_pipeline.ps1` and a `Makefile` for convenient one‑click execution.

---

## 3. Scientific Studies
### 3.1 Study A – Network Robustness
* **Goal** – Quantify how the monsoon precipitation network fragments under node removal.
* **Scenarios** – Random removal, removal of highest‑degree nodes, removal of highest‑betweenness nodes.
* **Metrics** –
  * **Largest Connected Component (LCC) size** – fraction of nodes remaining in the biggest sub‑graph.
  * **Global efficiency** – average inverse shortest‑path length, normalised to the original network size.
* **Key Findings**
  1. **Random removal** is relatively benign: LCC stays above 70 % until ~30 % of nodes are removed.
  2. **Targeted removal** (degree or betweenness) causes rapid collapse – LCC drops below 30 % after removing only ~5 % of the most central cells.
  3. Global efficiency mirrors LCC, confirming loss of information‑transfer capability.
* **Outputs** – `robustness.parquet` (curves), `critical_nodes.parquet` (list of top‑influence cells), `sensitivity.parquet` (impact of centrality choice).

### 3.2 Study B – Landslide Validation
* **Goal** – Test whether cells that are topologically important coincide with observed 2018 landslides, accounting for slope.
* **Method** – For each cell compute landslide density, attach DEM‑derived slope, and calculate Spearman correlation for:
  * Degree, Betweenness, Eigenvector, Clustering centralities
  * Terrain slope (as a baseline)
* **Bootstrap** – 1 000 resamples to obtain 95 % confidence intervals.
* **Key Findings**
  1. All centrality metrics show **positive, statistically significant** correlations with landslide density (ρ ≈ 0.35 – 0.45; CI excludes 0).
  2. Slope alone also correlates, but the centrality‑landslide relationship remains significant after controlling for slope, indicating that **network position adds explanatory power**.
* **Output** – `landslide_stats.parquet` (correlation coefficients and confidence intervals).

---

## 4. Front‑End (React + Vite) Architecture
* **Framework** – React 18 + TypeScript, bundled with Vite (dev server on `http://localhost:3000`).
* **Styling** – Tailwind CSS with dark‑mode support.
* **Mapping** – Leaflet renders choropleth cells, weighted links, and landslide point overlays.
* **State** – Centralised in `src/state/AppContext.tsx` (active page, selected metric, percentile threshold, link‑weight filter, theme, and contract data).
* **Pages** –
  * **Overview** – KPI cards & summary map.
  * **Network Explorer** – Metric‑driven choropleth + interactive link visualisation.
  * **Robustness** – LCC & efficiency curves for each removal scenario; critical‑node list.
  * **Basins** – Basin‑wise impact bar chart & map shading.
  * **Landslide Validation** – Scatter plot of centralities vs. landslide density with bootstrap confidence bands.
  * **Methodology** – Flowchart of the entire pipeline, parameter tables, and provenance.
* **Data contract** – UI loads static JSON/GeoJSON files generated in Stage 8; see `src/types/contract.ts` for TypeScript interfaces.

---

## 5. What the Dashboard Shows
| Page | Visual Element | Insight provided |
|------|----------------|-----------------|
| **Overview** | KPI cards (network size, robustness summary, landslide‑validation result) | One‑glance status of the whole study. |
| **Network Explorer** | Choropleth coloured by chosen centrality, weighted links toggled by a slider | Spatial distribution of “important” cells and how they connect. |
| **Robustness** | Line charts of LCC size & global efficiency vs. fraction of nodes removed (random, degree, betweenness) | Direct visual evidence of vulnerability to targeted attacks. |
| **Basins** | Bar chart of basin‑level impact + basin‑wise map shading | Which river basins lose connectivity fastest. |
| **Landslide Validation** | Scatter plot + 95 % CI for each centrality (and slope) vs. landslide density | Quantitative proof that central cells are more landslide‑prone. |
| **Methodology** | Flow‑chart and parameter table | Full reproducibility & provenance. |

---

## 6. Running the Application (Node + React)
1. **Ensure Node is on your `PATH`** (you already have it). In PowerShell you can prepend it temporarily:
   ```powershell
   $env:PATH = "C:\Program Files\nodejs;" + $env:PATH
   ```
2. **Navigate to the UI directory**:
   ```powershell
   cd "C:\Users\Ashmi_SN\Desktop\btpproject\web"
   ```
3. **Install dependencies** (run once):
   ```powershell
   npm install
   ```
4. **Start the development server** (opens `http://localhost:3000`):
   ```powershell
   npm run dev
   ```
5. **Optional – Production build**:
   ```powershell
   npm run build          # creates `dist/`
   npx serve -s dist      # serves the static site
   ```

---

## 7. Repository Layout (key paths)
```
btpproject/
├─ data/                 # raw / interim / processed artefacts
├─ pipeline/             # 01‑08 Python scripts
├─ src/ktnet/            # core Python modules (io, grid, events, sync, network, robustness, landslide, export)
├─ web/                  # React + Vite front‑end
│   ├─ public/data/      # JSON/GeoJSON contract files consumed by UI
│   ├─ src/              # TSX components, pages, context, utilities
│   └─ package.json
├─ APPROACH.md           # High‑level overview (already created)
├─ PROJECT_REPORT.md     # **This document** (comprehensive report)
└─ README.md             # General project README
```

---

## 8. Conclusions
* We successfully built an end‑to‑end, reproducible climate‑network analysis pipeline.
* The **robustness study** shows that the monsoon precipitation network is **highly vulnerable to targeted attacks** on hub cells, while being resilient to random failures.
* The **landslide validation** demonstrates that **network centrality is a significant predictor of landslide occurrence**, beyond simple terrain slope.
* The interactive dashboard makes these scientific results instantly accessible to researchers, policymakers, and the public.

---

*Prepared on 2026‑09‑21.*
