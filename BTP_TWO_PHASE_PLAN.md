# Bachelor Thesis Project (BTP): Two-Phase Execution & Evaluation Report

**Project Title:** Vyuham: Kerala Climate Network — Complex System Science, Spatial Network Robustness, and Extreme Precipitation Hazard Mapping  
**Student Name:** Ashmi S N  
**Academic Year:** 2026  
**Evaluation Scope:** Phase 1 (Current Term) Completion Report & Phase 2 (Next Term) Research Roadmap  

---

## 1. Project Overview & Motivation
Kerala experiences severe, recurring hydrometeorological disasters driven by extreme South Asian summer monsoon (JJAS) precipitation (e.g., 2018 catastrophic floods and Wayanad/Idukki debris flows). Conventional weather analysis treats meteorological grid points as independent stations. 

**Vyuham** introduces a **complex network and teleconnection approach** to model Kerala's climate system:
1. Transforming gridded spatio-temporal rainfall data into an **event-synchronized complex network**.
2. Quantifying topological structural vulnerability via **percolation and targeted node removal**.
3. Validating the physical significance of network hubs against **high-resolution 2018 landslide inventories**.
4. Developing an **interactive, reproducible GIS dashboard** for scientific inspection and disaster mitigation planning.

---

## 2. Phase 1 (Term 1) — Completed Milestones & Accomplishments

Phase 1 focused on building the mathematical formulation, pipeline infrastructure, exploratory network analytics, empirical validation, and the core interactive visualization platform.

### A. Data Engineering & Geospatial Pipeline (Stages 01–03)
* **High-Resolution Meteorological Integration:** Acquired and harmonized 40 years of India Meteorological Department (IMD) gridded daily rainfall data ($0.25^\circ \times 0.25^\circ$, 1981–2020).
* **Topographical & Catchment Mapping:** Built a Kerala land-sea boundary mask intersecting 103 spatial grid cells with major river basin polygons (Periyar, Bharathapuzha, Pamba, Chaliyar, etc.) and SRTM 30m Digital Elevation Model (DEM) slope values.
* **Nonlinear Extreme Event Extraction:** Isolated wet-day extremes using 90th, 95th, and 97th percentile thresholds during the June–September (JJAS) monsoon seasons, standardizing event series across all spatial cells.

### B. Network Construction & Centrality Algorithms (Stages 04–05)
* **High-Performance Event Synchronization:** Formulated an accelerated pairwise event synchronization (ES) algorithm using Numba (`Q_{i,j}` calculation with delay dynamics $\tau_{max} = 10$ days).
* **Network Pruning & Topology:** Retained the top 5% strongest statistically significant synchrony teleconnections ($n = 103$ nodes, $m = 265$ directed/undirected edges).
* **Graph Centrality Computations:** Calculated four fundamental graph-theoretic centralities for every cell:
  * **Degree Centrality:** Direct spatial synchrony density.
  * **Betweenness Centrality:** Information flow and precipitation bridge hubs.
  * **Clustering Coefficient:** Local cohesion and micro-catchment synchrony.
  * **Eigenvector Centrality:** Influence connected to other critical regional hubs.

### C. Scientific Investigation & Empirical Proving (Stages 06–07)
* **Study A — Network Fragility & Attack Vulnerability:**
  * Implemented Monte Carlo random failure versus targeted hub removal (degree-ordered and betweenness-ordered).
  * Monitored Largest Connected Component (LCC) decay and network global efficiency ($E_{glob}$).
  * **Proved:** The network is scale-free-like in vulnerability—highly resilient to random loss, but undergoes abrupt percolation collapse (LCC drops $>70\%$) when removing fewer than $5\%$ of top-ranked hubs.
* **Study B — Empirical Hazard Validation with 2018 Landslides:**
  * Geospatially overlaid the Geological Survey of India (GSI) 2018 Kerala landslide inventory onto the 103 cells.
  * Executed 1,000-iteration bootstrapped Spearman rank correlations ($\rho$).
  * **Proved:** Precipitation network centralities exhibit strong, statistically significant correlations ($\rho \approx 0.35 - 0.45, p < 0.001$) with observed landslide densities.
  * Even after stratifying for terrain slope (DEM), network betweenness provides statistically significant explanatory power for landslide hotspots.

### D. Zero-Backend Interactive GIS Dashboard (Stage 08 & Web UI)
* Built a responsive **React 18 + TypeScript + Vite + Tailwind CSS** dashboard (`web/`).
* Implemented multi-layer Leaflet GIS mapping featuring:
  * **Choropleth heatmaps** with Viridis and Vulnerability color ramps.
  * **Watermark-free, high-resolution scientific GIS tiles:** Esri Dark Canvas, Satellite Imagery (Western Ghats terrain), and Topo basemaps.
  * **Interactive Overlays:** Synchrony links (filtered by link-weight slider), 2018 Landslide point clusters, and River Basin boundaries.
* Designed 6 dedicated analytical views: *Overview, Network Explorer, Robustness (Study A), Basins Impact, Landslide Validation (Study B),* and *Methodology & Data Provenance*.
* Built 12-test comprehensive test suite (`pytest`) guaranteeing data contract compliance and numerical monotonicity.

---

## 3. Summary of Key Findings for Phase 1 Presentation

| Research Question | Finding in Phase 1 | Academic Significance |
| :--- | :--- | :--- |
| **Is the monsoon synchrony network uniform?** | No. Synchronization is concentrated along the Western Ghats windward ridges (Idukki, Wayanad, Palakkad gap). | Identifies natural hydrometeorological corridors across Kerala. |
| **How resilient is regional rainfall connectivity?** | Highly resilient to random disruptions, but critically vulnerable to targeted removal of top 5% hubs. | Identifies bottleneck catchment zones where localized anomalies have state-wide cascading impact. |
| **Does graph centrality correlate with real hazards?** | Yes, significant correlation ($\rho \approx 0.35 - 0.45$) with 2018 landslide clusters, retaining significance beyond slope alone. | Proves that complex network topology is a viable predictive feature for spatial disaster risk assessment. |

---

## 4. Phase 2 (Term 2) — Revised Core: Periyar Basin Case Study

Phase 2 focuses the broad statewide methodology down into an in-depth, defensible hydrological case study: **The Periyar Basin (Idukki to Ernakulam)**.

### Research Question
*Does the extreme-rainfall synchronization structure of the Periyar basin change during the catastrophic 2018 monsoon, and which cells/sub-regions are structurally critical for its connectivity?*

### Why Periyar?
- **High-Stakes Geography:** Kerala's longest river; hosts critical reservoirs (Idukki and Mullaperiyar dams); severely inundated in August 2018.
- **Unified Narrative:** Spans high-elevation Western Ghats (landslide hotspots in Idukki) to coastal lowlands (urban flooding in Ernakulam/Kochi), tying Study A (robustness) and Study B (landslides) into a coherent, defensible story.
- **Feasible Scope:** A focused single-basin study provides high scientific rigor and defensibility for a BTP defense.

```
Phase 1 (Completed)                     Phase 2 Core: Periyar Basin Case Study
┌─────────────────────────┐             ┌───────────────────────────────────────────┐
│ • Statewide Grid (103)  │             │ 1. Extract Periyar Subnetwork vs. Null    │
│ • Static ES Matrix      │   ──────►   │ 2. Event-Window: 2018 vs. Climatology     │
│ • State Robustness (A)  │             │ 3. Within-Basin Robustness & Percolation  │
│ • Landslide Valid. (B)  │             │ 4. Upper-Basin Landslide Controls (v2)    │
│ • Full GIS Dashboard    │             │ 5. Dedicated "Periyar" Dashboard View     │
└─────────────────────────┘             └───────────────────────────────────────────┘
```

### Core Components
1. **Basin Subnetwork & Null Model:**
   - Extract Periyar cells from the existing grid (`grid.py`).
   - Compare subnetwork link density, clustering, and centrality distributions against a null model of randomly sampled, same-sized cell subsets from the statewide network.
2. **Event-Window Comparative Analysis:**
   - Construct ES networks for (a) Climatological baseline (JJAS 1981–2017) and (b) Monsoon 2018 (specifically the 1–31 August 2018 window).
   - Track link density shifts and hub rank shifts using permutation/shuffle null tests to ensure changes are not small-sample noise.
3. **Within-Basin Robustness:**
   - Restrict the node removal experiments (`robustness.py`) strictly to the Periyar subgraph.
   - Determine the basin's percolation threshold and pinpoint intra-basin bottleneck cells.
4. **Upper-Basin Landslide Controls (Study B v2):**
   - Apply the Study B v2 ladder (`landslide_controls.py`) with spatial block bootstrapping on upper Periyar catchment cells.
5. **Interactive Dashboard Extension:**
   - Add a dedicated **"Periyar Basin"** page to the React UI displaying the subnetwork map, 2018 vs. climatology delta, and critical cells.

### Honest Scientific Limitations & Risks
- **Spatial Resolution:** Periyar spans a moderate number of 0.25° cells; spatial buffers and bootstrap confidence intervals will be reported, avoiding over-claiming.
- **Single-Year Event:** 2018 is treated strictly as an extreme historical case study, not a universal climatological law.
- **Topological vs. Hydrological:** Network synchrony reflects meteorological teleconnections, not physical channel hydraulic routing.

### Future Work (Post-BTP / Extension)
- Spatio-temporal Graph Neural Networks (ST-GNN) for predictive rainfall forecasting.
- Real-time automated early-warning alerts and cloud microservice deployment.
- Dam inflow/discharge correlation and flood-damage layer integration.

---

## 5. Deliverables Checklist for This Term Evaluation

* [x] **Complete Data Pipeline (`pipeline/01` to `08`):** Fully reproducible with `run_pipeline.ps1`.
* [x] **Core Package (`src/ktnet/`):** Clean, modular, typed Python implementation with Numba acceleration.
* [x] **Test Suite (`tests/`):** 12 unit and integration tests passing.
* [x] **Frontend Dashboard (`web/`):** Interactive React GIS dashboard with zero watermarks, multiple basemap options, and live inspection drawers.
* [x] **Automated Documentation & Word Compiler:** `generate_report.py` to compile screenshots into `BTP_Report.docx`.
* [x] **Comprehensive Written Reports:** `PROJECT_REPORT.md`, `APPROACH.md`, and `RUN_INSTRUCTIONS.md`.
