# Project Approach Overview

## 1. Goal & Context
The **Kerala Climate Network (Vyuham)** project builds a synchronized monsoon precipitation network across Kerala’s river basins, quantifies its robustness, and validates the network against observed landslide events.  The workflow consists of a pure‑Python data‑processing pipeline that produces a set of **contract files** (JSON/GeoJSON) consumed by a zero‑backend **React + Vite** web dashboard.

---

## 2. End‑to‑End Pipeline (Stages 1‑8)
| Stage | Script | Primary Input | Primary Output | Description |
|------|--------|---------------|----------------|-------------|
| 01 | `pipeline/01_download_data.py` | Remote URLs (rainfall, DEM, landslide data) | `data/raw/` files | Downloads all raw scientific datasets.
| 02 | `pipeline/02_build_grid.py` | Raw raster & basin shapefiles | `data/interim/cells.parquet` | Constructs a 0.25° grid, masks land cells, joins basins.
| 03 | `pipeline/03_extract_events.py` | Grid, precipitation series | `data/interim/events.npz` | Extracts extreme JJAS wet‑day events per cell.
| 04 | `pipeline/04_sync_matrix.py` | Event indices per cell | `data/interim/es_matrix.npy` | Computes pairwise event‑synchronisation matrix.
| 05 | `pipeline/05_build_network.py` | Synchronisation matrix | `data/processed/network.graphml`, `metrics.parquet` | Builds the weighted network, thresholds top 5 % links, calculates centralities.
| 06 | `pipeline/06_robustness_study.py` | Network, centralities | `robustness.parquet`, `basin_impact.parquet`, `critical_nodes.parquet`, `sensitivity.parquet` | Simulates random/targeted node removal, measures LCC size & global efficiency, estimates basin‑level impact.
| 07 | `pipeline/07_landslide_validation.py` | Network, landslide points, DEM slope | `landslide_stats.parquet` | Bootstrapped Spearman correlation between centralities (and slope) and landslide density.
| 08 | `pipeline/08_export_ui.py` | All intermediate artefacts | `web/public/data/*.json` & `*.geojson` | Serialises the **data contract** for the UI (see *Section 4*).

---

## 3. Scientific Studies
### Study A – Robustness
* **What** – Quantifies how the network fragments under node removal (random, degree‑based, betweenness‑based).  
* **Metrics** – Largest Connected Component (LCC) size, global efficiency (normalized by the original network size).  
* **Key outputs** – `robustness.parquet` (curves), `critical_nodes.parquet` (most influential nodes), `sensitivity.parquet` (how centrality choice changes results).

### Study B – Landslide Validation
* **What** – Tests whether high‑centrality cells coincide with observed 2018 landslides, accounting for slope.
* **Method** – Bootstrapped Spearman correlation for each centrality metric and for slope alone.
* **Key output** – `landslide_stats.parquet` (correlation coefficients, 95 % confidence intervals).

---

## 4. Web UI Architecture
* **Framework** – React 18 + TypeScript, bundled with **Vite** (dev server on `http://localhost:3000`).
* **Styling** – Tailwind CSS, dark‑mode support.
* **Mapping** – Leaflet with raster & vector layers; choropleth visualises the selected metric, links are drawn for weights above a user‑set threshold.
* **Pages** – Overview, Network Explorer, Robustness, Basins, Landslide Validation, Methodology.
* **State Management** – React Context (`src/state/AppContext.tsx`) holds active page, selected metric, percentile threshold, link‑weight filter, theme, and the contract data loaded via `src/lib/dataLoader.ts`.
* **Data Contract** – The UI consumes the JSON/GeoJSON files generated in **Stage 8**; see `web/src/types/contract.ts` for the TypeScript interfaces.

---

## 5. Running the Application
### Prerequisites
1. **Node.js** (v24 or later) and **npm** must be on your `PATH`.  On Windows you can add the installation folder, e.g.:
   ```powershell
   $env:PATH = "C:\Program Files\nodejs;" + $env:PATH
   ```
2. The Python pipeline has already been executed (the contract files live under `web/public/data/`).

### Step‑by‑Step
```powershell
# 1️⃣ Change to the UI directory
cd "C:\Users\Ashmi_SN\Desktop\btpproject\web"

# 2️⃣ Install JavaScript dependencies (run once)
npm install

# 3️⃣ Start the development server (opens http://localhost:3000)
npm run dev
```
The browser will automatically open and display the dashboard.  All visualisations pull data from the generated contract files.

### Production Build (optional)
```powershell
npm run build   # creates a static site in the `dist/` folder
# Serve the static files with any HTTP server, e.g.:
npx serve -s dist
```

---

## 6. Quick Reference Commands
| Action | Command |
|--------|---------|
| Re‑run the full Python pipeline | `powershell -File run_pipeline.ps1` |
| Install UI dependencies | `npm install` |
| Launch UI (dev) | `npm run dev` |
| Build static UI | `npm run build` |
| Serve built UI | `npx serve -s dist` |

---

**That’s the complete approach and the exact steps to get the application running.**
