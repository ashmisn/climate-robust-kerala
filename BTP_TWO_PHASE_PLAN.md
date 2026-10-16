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

## 4. Phase 2 (Term 2) — Proposed Scope & Next Steps

Phase 2 will transition the project from **diagnostic/structural network analysis** to **predictive modeling, dynamic forecasting, and decision-support operationalization**.

```
Phase 1 (Completed)                     Phase 2 (Proposed Roadmap)
┌─────────────────────────┐             ┌─────────────────────────┐
│ • Historical IMD 1981-20│             │ • Sub-seasonal Forecasts│
│ • Static ES Matrix      │   ──────►   │ • Time-varying Networks │
│ • Structural Robustness │             │ • GNN / Spatio-Temporal │
│ • 2018 Landslide Align  │             │ • Early Warning Index   │
│ • Interactive GIS UI    │             │ • Policy & Cloud Deploy │
└─────────────────────────┘             └─────────────────────────┘
```

### Milestone 1: Dynamic & Time-Varying Climate Networks
* **Moving-Window Network Analysis:** Replace the aggregate 40-year static network with dynamic 30-day sliding window networks for individual monsoon seasons (e.g., comparing drought years like 2016 vs. mega-flood years like 2018 and 2019).
* **Lead-Lag Directed Teleconnections:** Incorporate directed synchrony delays to trace the spatial propagation vectors of rainstorms traveling from south to north along the coast and Western Ghats.

### Milestone 2: Machine Learning & Graph Neural Network (GNN) Risk Prediction
* **Spatio-Temporal Graph Neural Networks (ST-GNN):** Use the adjacency matrix created in Phase 1 as the graph topology for a GNN/LSTM hybrid model to predict 24h–72h localized extreme precipitation and flash flood risks.
* **Multi-Factor Susceptibility Model:** Integrate additional physical covariates into each node: soil moisture indices (SMAP/ERA5-Land), lithology, land-use land-cover (LULC), and cumulative antecedent rainfall.

### Milestone 3: Real-Time Early Warning & Critical Node Alert System
* **Network-Based Early Warning Indicator:** Develop an automated metric (e.g., rapid spike in regional clustering coefficient or sudden drop in network diameter) that flags imminent synchronized convective storms 2–3 days in advance.
* **Basin-Wise Vulnerability Index (B-VI):** Deliver a composite vulnerability score for Kerala's 44 river basins, assisting Kerala State Disaster Management Authority (KSDMA) and dam operators (e.g., Idukki and Mullaperiyar reservoir water release scheduling).

### Milestone 4: Production Deployment & Policy Toolkit
* **Automated Data Ingestion:** Connect pipeline to IMD real-time API or GPM (Global Precipitation Measurement) satellite feeds.
* **Public Cloud Deployment:** Containerize the pipeline and UI with Docker, deploying to a cloud hosting platform (e.g., Vercel / AWS) with public access.
* **Academic Publication:** Format results for submission to a peer-reviewed geosciences / complex systems journal (e.g., *Chaos*, *Nonlinear Processes in Geophysics*, or *Scientific Reports*).

---

## 5. Deliverables Checklist for This Term Evaluation

* [x] **Complete Data Pipeline (`pipeline/01` to `08`):** Fully reproducible with `run_pipeline.ps1`.
* [x] **Core Package (`src/ktnet/`):** Clean, modular, typed Python implementation with Numba acceleration.
* [x] **Test Suite (`tests/`):** 12 unit and integration tests passing.
* [x] **Frontend Dashboard (`web/`):** Interactive React GIS dashboard with zero watermarks, multiple basemap options, and live inspection drawers.
* [x] **Automated Documentation & Word Compiler:** `generate_report.py` to compile screenshots into `BTP_Report.docx`.
* [x] **Comprehensive Written Reports:** `PROJECT_REPORT.md`, `APPROACH.md`, and `RUN_INSTRUCTIONS.md`.
