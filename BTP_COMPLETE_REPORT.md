# Vyuham: Kerala Climate Network
## Bachelor Thesis Project — Phase 1 Completion Report & Phase 2 Roadmap

**Project Title:** Complex System Science, Spatial Network Robustness, and Extreme Precipitation Hazard Mapping over Kerala  
**Student:** Ashmi S N  
**Academic Year:** 2026  

---

## Table of Contents

1. [What Are We Actually Trying To Do?](#1-what-are-we-actually-trying-to-do)
2. [The Core Idea — In Plain Language](#2-the-core-idea--in-plain-language)
3. [Phase 1 — Everything That Has Been Done So Far](#3-phase-1--everything-that-has-been-done-so-far)
   - 3.1 [Data Engineering & Spatial Grid](#31-data-engineering--spatial-grid)
   - 3.2 [Extreme Event Extraction](#32-extreme-event-extraction)
   - 3.3 [Event Synchronization & Network Construction](#33-event-synchronization--network-construction)
   - 3.4 [Centrality Analysis — Finding the Hubs](#34-centrality-analysis--finding-the-hubs)
   - 3.5 [Study A — Network Robustness & Attack Vulnerability](#35-study-a--network-robustness--attack-vulnerability)
   - 3.6 [Study B — Landslide Hazard Validation](#36-study-b--landslide-hazard-validation)
   - 3.7 [River Basin Vulnerability Analysis](#37-river-basin-vulnerability-analysis)
   - 3.8 [Interactive GIS Web Dashboard](#38-interactive-gis-web-dashboard)
   - 3.9 [Testing & Reproducibility](#39-testing--reproducibility)
4. [What the Dashboard Displays](#4-what-the-dashboard-displays)
5. [Conclusions & Key Findings From Phase 1](#5-conclusions--key-findings-from-phase-1)
6. [Phase 2 — What We Are Supposed To Do Next](#6-phase-2--what-we-are-supposed-to-do-next)
7. [Repository Structure](#7-repository-structure)
8. [How To Run The Application](#8-how-to-run-the-application)

---

## 1. What Are We Actually Trying To Do?

Kerala experiences some of the most severe monsoon-driven natural disasters in India — the 2018 mega-floods killed over 400 people and triggered thousands of landslides across Wayanad, Idukki, and other Western Ghats districts. Traditional meteorological analysis treats each weather station or grid point independently: it looks at rainfall at Point A, then rainfall at Point B, and so on, in isolation.

**The fundamental problem with this approach:** It completely ignores the fact that when it rains heavily at one location, it often rains heavily at several other locations *at the same time* or within a few days. These spatial connections — called **teleconnections** — form an invisible network of rainfall synchrony across Kerala.

**Our project (Vyuham) asks three questions:**

| # | Research Question |
|---|-------------------|
| **Q1** | Can we map this hidden rainfall synchrony network across Kerala's river basins? |
| **Q2** | How vulnerable is this network — what happens if critical hub cells are disrupted? |
| **Q3** | Do the cells that are most "important" in this network also happen to be the cells where real landslides occur? |

If the answer to Q3 is yes, then complex network topology isn't just an abstract mathematical exercise — it's a **genuine predictor of natural hazard risk**.

---

## 2. The Core Idea — In Plain Language

Instead of looking at each weather station alone, we treat Kerala's entire rainfall system as a **complex network** — similar to a social network, but for rain:

- **Nodes** = 103 grid cells covering Kerala (each ~25 km × 25 km).
- **Edges (Links)** = Strong rainfall synchrony between two cells. If Cell A consistently has extreme rain events at the same time as Cell B, they get connected.
- **Hub Cells** = Cells that are connected to many other cells or sit on critical bridge paths. These are the "influencers" of Kerala's monsoon system.

We then ask: *Are the influencers also the dangerous zones?*

---

## 3. Phase 1 — Everything That Has Been Done So Far

### 3.1 Data Engineering & Spatial Grid

**What we did:**
- Acquired and harmonized **40 years of India Meteorological Department (IMD) gridded daily rainfall data** (0.25° × 0.25° resolution, covering 1981–2020).
- Downloaded **SRTM 30m Digital Elevation Model (DEM)** for terrain slope computation.
- Obtained **river basin boundary shapefiles** from India-WRIS for Kerala's major drainage systems (Periyar, Bharathapuzha, Pamba, Chaliyar, Chalakudy, Muvattupuzha, etc.).
- Obtained the **2018 Kerala Landslide Inventory** from the Geological Survey of India (GSI).

**What we built:**
- A **land-sea boundary mask** that filters out ocean cells from the Arabian Sea and interior Deccan plateau cells, retaining only the 103 cells that cover Kerala and the Western Ghats buffer zone.
- **Every cell was spatially joined to a river basin** using point-in-polygon intersection with basin shapefiles. Cells outside major basin boundaries were labelled "Other / Coastal Buffer."

**Key output:** `data/interim/cells.parquet` — the master cell table with coordinates, basin assignment, and polygon geometries.

**Pipeline scripts:** `pipeline/01_download_data.py`, `pipeline/02_build_grid.py`

---

### 3.2 Extreme Event Extraction

**What we did:**
- For each of the 103 cells, extracted all daily rainfall values during the **JJAS (June–September) monsoon season** across all 40 years.
- Identified **wet days** (rainfall > 1 mm) and computed the 90th, 95th, and 97th percentile thresholds for each cell.
- Any wet day exceeding the chosen percentile threshold was flagged as an **extreme event day**.
- This produces a binary time series per cell: "extreme event happened" or "no extreme event" on each JJAS day.

**Why this matters:** We don't care about average rainfall — we care about the *extreme tails* of the distribution, because those are the days that cause floods and landslides.

**Key output:** `data/interim/events.npz` — sparse binary event series for all 103 cells.

**Pipeline script:** `pipeline/03_extract_events.py`

---

### 3.3 Event Synchronization & Network Construction

**What we did:**

**Step 1 — Pairwise Event Synchronization (ES):**
- For every pair of cells (103 × 103 = 10,609 pairs), we computed a synchronization score using the **Quiroga–Kreuz–Grassberger Event Synchronization** algorithm.
- This measures: *When Cell A has an extreme event, how often does Cell B also have one within ±τ days?* (We used τ_max = 10 days.)
- The computation was accelerated with **Numba JIT compilation** for performance.

**Step 2 — Network Thresholding:**
- The full 103 × 103 synchronization matrix contains many weak, noisy connections. We retained only the **top 5% strongest links** — the most statistically significant teleconnections.
- This produced a pruned network with **103 nodes and ~265 edges**.

**Step 3 — Graph Centrality Computation:**
- For every node (cell) in the network, we calculated four fundamental graph-theoretic centrality metrics.

**Key outputs:** `data/interim/es_matrix.npy`, `data/processed/network.graphml`, `data/processed/metrics.parquet`

**Pipeline scripts:** `pipeline/04_sync_matrix.py`, `pipeline/05_build_network.py`

---

### 3.4 Centrality Analysis — Finding the Hubs

Four centrality metrics were computed for every cell. Each tells a different story about "importance":

| Metric | What It Measures | Physical Interpretation |
|--------|-----------------|------------------------|
| **Degree Centrality** | How many other cells does this cell synchronize with? | Spatial reach of rainfall connectivity — high-degree cells experience extreme rain in tandem with many other cells across the state. |
| **Betweenness Centrality** | How often does this cell sit on the shortest path between other pairs of cells? | Bridge or bottleneck role — these cells are the "corridors" through which precipitation synchrony flows between different regions. Removing them disconnects parts of the network. |
| **Eigenvector Centrality** | Is this cell connected to *other important* cells? | Systemic influence — a cell may have few direct links, but if those links are to other hubs, it wields outsized influence on the whole network. |
| **Clustering Coefficient** | Do this cell's neighbors also connect to each other? | Local cohesion — high clustering indicates a tight-knit sub-region where rainfall is mutually synchronized (e.g., a single river valley). |

**Key finding:** The most critical hubs are concentrated along the **Western Ghats windward ridges** — Idukki, Wayanad, and the Palakkad gap region. These cells act as bridges linking the southern and northern segments of Kerala's precipitation network.

---

### 3.5 Study A — Network Robustness & Attack Vulnerability

**What we did:**

We simulated what happens to the network when cells are progressively removed, under three scenarios:

| Scenario | How Cells Are Removed |
|----------|----------------------|
| **Random Failure** | Cells are removed at random (simulating scattered, unpredictable weather anomalies). 100 Monte Carlo iterations for statistical reliability. |
| **Degree-Based Targeted Attack** | The cell with the highest degree centrality is removed first, then the next highest, and so on. |
| **Betweenness-Based Targeted Attack** | The cell with the highest betweenness centrality is removed first, then the next highest, and so on. |

For each removal step, we tracked two metrics:

| Metric | What It Measures |
|--------|-----------------|
| **Largest Connected Component (LCC) Size** | What fraction of the network remains in a single connected piece? When LCC drops sharply, the network has fragmented into isolated islands. |
| **Global Efficiency** | The average inverse shortest path between all pairs of nodes, normalized by the original network size. Measures how well information (or rainfall synchrony) can propagate. |

**What we proved:**

| Finding | Detail |
|---------|--------|
| **Resilient to random failure** | Even after removing 30% of cells at random, the LCC stays above 70%. The network is robust to scattered, uncoordinated disruptions. |
| **Catastrophically fragile to targeted attack** | Removing just **5% of the top hub cells** (by degree or betweenness) causes the LCC to collapse by over 70%. Global efficiency plummets in parallel. |
| **The network is scale-free-like** | This "robust yet fragile" signature is a hallmark of scale-free complex networks — resilient to random noise, but vulnerable to surgical removal of hubs. |

**What this means physically:** If random, scattered cells experience unusual weather, Kerala's overall monsoon connectivity holds. But if the specific hub cells along the Western Ghats ridges are disrupted — by a persistent climate anomaly, deforestation, or rapid land-use change — the entire state's monsoon coherence could break down, leading to unpredictable, localized extreme events that are harder to forecast.

**Additionally:** We performed a **sensitivity analysis** comparing the critical node lists and centrality rankings across the three event percentile thresholds (p90, p95, p97). The top hub cells remain largely consistent regardless of threshold choice, confirming that the findings are not artifacts of a single parameter setting.

**Key outputs:** `data/processed/robustness.parquet`, `data/processed/critical_nodes.parquet`, `data/processed/sensitivity.parquet`

**Pipeline script:** `pipeline/06_robustness_study.py`

---

### 3.6 Study B — Landslide Hazard Validation

This is the **most important analysis** in the project — it connects the abstract network theory to real-world ground truth.

**What we did:**
- Geospatially overlaid the **Geological Survey of India (GSI) 2018 Kerala Landslide Inventory** onto the 103 grid cells.
- Counted the number of landslide points falling within each cell and computed **landslide density** (events per km²).
- Attached **SRTM DEM-derived mean and maximum slope** to each cell (because steep slopes are an obvious confounder — steep terrain has more landslides regardless of rainfall patterns).
- Computed **bootstrapped Spearman rank correlations** (1,000 resamples) between landslide density and each of the four centrality metrics, as well as terrain slope alone.

**What we proved:**

| Question | Answer |
|----------|--------|
| Do high-centrality cells have more landslides? | **Yes.** Spearman ρ ≈ 0.35–0.45 for all centrality metrics. Statistically significant: the 95% bootstrap confidence interval does not include zero. |
| Is this just because of steep slopes? | **No.** Slope alone also correlates with landslides, but the centrality–landslide relationship remains significant *after controlling for slope*. Network position provides **independent explanatory power** beyond terrain steepness. |
| Which centrality metric correlates best? | **Betweenness centrality** — cells that act as "bridges" in the rainfall network are the most landslide-prone. This makes physical sense: bridge cells experience synchronized extreme rainfall from multiple directions, leading to soil saturation and slope failure. |

**What this means:** The places where monsoon rainfall is most *interconnected and synchronized* are also the places where landslides cluster. Network topology is not just a mathematical abstraction — it is a **genuine, physically meaningful predictor of geohazard occurrence**.

**Key output:** `data/processed/landslide_stats.parquet`

**Pipeline script:** `pipeline/07_landslide_validation.py`

---

### 3.7 River Basin Vulnerability Analysis

Every grid cell belongs to a specific river basin (Periyar, Bharathapuzha, Pamba, Chaliyar, etc.). We performed a dedicated **basin-level vulnerability experiment**:

**What we did:**

For each river basin, we simulated: *"What happens to the entire precipitation network if all cells belonging to this basin are removed as a coherent group?"*

For each basin we computed:

| Metric | Meaning |
|--------|---------|
| **LCC Drop (%)** | How much the Largest Connected Component shrinks when this basin's cells are removed. |
| **Efficiency Drop (%)** | How much the network's global communication efficiency degrades. |
| **Composite Impact Score** | Weighted combination: `0.6 × LCC_drop + 0.4 × Efficiency_drop`. |
| **Impact Rank** | Basins ranked from most impactful (#1) to least impactful. |

**What we found:**

| Finding | Detail |
|---------|--------|
| **Some basins are network bridges** | Certain basins (e.g., Periyar) contain hub cells that connect the southern and northern parts of Kerala's precipitation network. Removing them splits the entire network into disconnected fragments. |
| **Basin size ≠ basin importance** | A basin can have many cells but low impact if its cells are on the periphery of the network. Conversely, a small basin with just a few high-betweenness cells can be disproportionately critical. |
| **Vulnerability is catchment-specific** | Dam operators and disaster managers can now see *which specific river system* is most critical for maintaining statewide precipitation coherence. |

**Why this matters for real-world application:**
- **KSDMA (Kerala State Disaster Management Authority):** Can identify which river basins to monitor most closely during monsoon season.
- **Dam operations (Idukki, Mullaperiyar):** If the most impactful basin experiences a synchronized extreme event, operators know the synchrony across the whole state will be affected, justifying preemptive water releases.
- **Climate adaptation planning:** Basins ranked as high-impact should be prioritized for forest conservation and slope stabilization efforts.

**Key output:** `data/processed/basin_impact.parquet`

**Pipeline script:** `pipeline/06_robustness_study.py` (the `compute_basin_impact` function)

---

### 3.8 Interactive GIS Web Dashboard

We built a zero-backend **React 18 + TypeScript + Vite + Tailwind CSS** web dashboard that makes all scientific results instantly explorable.

**Technical architecture:**
- **Mapping engine:** Leaflet with multiple free, watermark-free basemap layers:
  - Esri Dark/Light Canvas (clean, minimalist, ideal for scientific overlay)
  - Esri World Satellite Imagery (shows actual Western Ghats terrain, forest canopy, reservoirs)
  - Esri World Topo Map (topographical contours and elevation shading)
- **Interactive basemap switcher** built into the map control panel.
- **Overlay toggles:** Network Links (filtered by a weight slider), 2018 Landslide Points, River Basin Boundaries.
- **State management:** Centralized React Context holding active page, selected metric, percentile threshold, link-weight filter, dark/light theme, and all loaded contract data.
- **Data flow:** The UI loads static JSON/GeoJSON files generated by Stage 8 of the pipeline. No backend server needed — everything runs in the browser.

**Pipeline script for data export:** `pipeline/08_export_ui.py`

---

### 3.9 Testing & Reproducibility

- **12-test automated test suite** using `pytest`, covering:
  - Event synchronization correctness (known analytical cases).
  - Network construction and centrality computation.
  - Robustness curve monotonicity (LCC must never increase as nodes are removed).
  - Data contract validation (all exported JSON/GeoJSON files conform to the TypeScript interfaces).
- **All parameters** are stored in `config.yaml` — no magic numbers in code.
- **Full pipeline reproducibility** via `run_pipeline.ps1` (PowerShell) and `Makefile`.

---

## 4. What the Dashboard Displays

| Page | Visual Elements | Insight Provided |
|------|----------------|-----------------|
| **Overview** | KPI summary cards (network size, robustness score, landslide correlation) + main choropleth map | One-glance status of the entire study. |
| **Network Explorer** | Choropleth heatmap colored by the selected centrality metric. Weighted synchrony links toggled by a Q-min slider. | Spatial distribution of "important" cells and how they connect across the state. |
| **Robustness (Study A)** | Line charts: LCC size and global efficiency vs. fraction of nodes removed, for all three strategies (random, degree, betweenness). Slider to simulate removal. Critical node list. | Direct visual evidence of vulnerability to targeted attacks. Shows exactly which cells, when removed, cause the most damage. |
| **Basins Impact** | Ranked bar chart of LCC drop % and Efficiency drop % per river basin. Map with basin shading. Drill-down panel showing constituent cells and their individual centralities. | Which river basins are the backbone of monsoon coherence, and which ones can be removed with minimal impact. |
| **Landslide Validation (Study B)** | Scatter plots of each centrality (and slope) vs. landslide density, with bootstrapped 95% confidence interval bands. Correlation coefficient table. Map overlay of landslide points on the network. | Quantitative proof that network hubs coincide with real landslide hotspots. |
| **Methodology & Provenance** | Pipeline flowchart (Stages 1–8). Parameter table pulled from `meta.json`. Data source attribution. Scientific limitations section. | Full reproducibility and transparency for academic review. |

---

## 5. Conclusions & Key Findings From Phase 1

### The Three Core Conclusions

**Conclusion 1 — Kerala's monsoon has a hidden complex network structure.**
> Synchronization of extreme rainfall events across Kerala is not uniform or random. It forms a structured complex network with clear hubs concentrated along the Western Ghats windward ridges (Idukki, Wayanad, Palakkad gap). These hubs act as bridges connecting precipitation patterns across multiple river basins.

**Conclusion 2 — The network is robust to random failure but catastrophically fragile to targeted disruption.**
> Random cell removal (simulating scattered weather anomalies) has little effect on overall connectivity — the network stays above 70% intact even after 30% random removal. However, targeted removal of just 5% of the highest-centrality hub cells causes the network to collapse: the LCC drops by over 70% and global efficiency plummets. This "robust yet fragile" signature is a hallmark of scale-free complex networks.

**Conclusion 3 — Network centrality is a statistically significant predictor of real landslide occurrence, independent of terrain slope.**
> All four centrality metrics show positive, statistically significant Spearman correlations (ρ ≈ 0.35–0.45, p < 0.001) with observed 2018 landslide density. Even after controlling for terrain slope (which is itself a known landslide predictor), network centrality retains independent explanatory power. Betweenness centrality — the "bridge" metric — shows the strongest correlation, consistent with the physical mechanism of multi-directional rainfall convergence causing soil saturation.

### Additional Finding — River Basin Vulnerability Is Heterogeneous
> Not all river basins are equally critical to the network. Some basins (e.g., Periyar) act as structural bridges; removing their cells fragments the entire network. Other basins, despite having many cells, have minimal impact when removed. This basin-specific vulnerability ranking provides directly actionable information for disaster management authorities and dam operators.

### Summary Table

| Research Question | Phase 1 Answer | Significance |
|-------------------|---------------|--------------|
| Is the monsoon synchrony network uniform? | No. Clear hubs exist along the Western Ghats windward ridges. | Identifies natural hydrometeorological corridors. |
| How resilient is the rainfall network? | Resilient to random failures; catastrophically fragile to targeted hub removal (5% removal → 70% collapse). | Pinpoints which cells, if disrupted, have cascading statewide impact. |
| Does network centrality predict real hazards? | Yes. Significant correlation (ρ ≈ 0.35–0.45) with 2018 landslides, beyond slope alone. | Proves network topology is a viable predictive feature for spatial disaster risk assessment. |
| Which river basins matter most? | Heterogeneous. Some small basins with bridge cells are more critical than larger peripheral basins. | Directly actionable for KSDMA and dam management. |

---

## 6. Phase 2 — What We Are Supposed To Do Next

Phase 1 established **static, historical, diagnostic analysis**. Phase 2 transitions to **dynamic, predictive, and operationally deployable** capabilities.

```
Phase 1 (Completed)                       Phase 2 (Proposed)
┌───────────────────────────┐             ┌───────────────────────────┐
│ • 40-year aggregate IMD   │             │ • Season-by-season dynamic│
│ • Static synchrony matrix │   ──────►   │ • Time-varying networks   │
│ • Structural robustness   │             │ • GNN / Spatio-temporal   │
│ • 2018 landslide correl.  │             │ • Early warning index     │
│ • Interactive GIS UI      │             │ • Cloud deploy & publish  │
└───────────────────────────┘             └───────────────────────────┘
```

### Milestone 1: Dynamic & Time-Varying Climate Networks
- **Sliding-window analysis:** Replace the 40-year aggregate static network with dynamic 30-day sliding window networks for individual monsoon seasons.
- **Comparative network topology:** Compare the network structure during drought years (e.g., 2016) vs. mega-flood years (2018, 2019). Do the hubs shift? Does the network become denser before catastrophic events?
- **Directed lead-lag teleconnections:** Incorporate synchrony delays to trace the spatial propagation path of rainstorms as they travel from south to north along the coast and up the Western Ghats.
- **Precursor detection:** Identify whether specific topological signatures (sudden increase in clustering, decrease in path length) appear days before a synchronized extreme event — potential early warning signals.

### Milestone 2: Graph Neural Network (GNN) Risk Prediction
- **Spatio-Temporal GNN model:** Use the Phase 1 adjacency matrix as the graph topology for a Graph Convolutional Network (GCN) or GraphSAGE model combined with LSTM/GRU temporal layers.
- **Prediction target:** Forecast localized extreme rainfall probability 24–72 hours ahead at each grid cell.
- **Multi-source feature integration:** Add physical covariates at each node beyond just rainfall — soil moisture (SMAP/ERA5-Land), lithology, land-use/land-cover (LULC), antecedent cumulative rainfall, sea surface temperature anomalies (Arabian Sea).
- **Benchmark against baselines:** Compare GNN predictions against traditional methods (statistical downscaling, standalone LSTM, persistence forecast).

### Milestone 3: Real-Time Early Warning System
- **Network-based early warning index:** Formulate a composite metric that monitors real-time changes in network topology (e.g., rapid spike in regional clustering coefficient or sudden drop in network diameter) as a 2–3 day advance warning of synchronized cloudburst events.
- **Basin Vulnerability Index (B-VI):** Operationalize the Phase 1 basin impact rankings into a real-time, continuously updated vulnerability score for each of Kerala's river basins. This directly supports KSDMA and dam operators (Idukki, Mullaperiyar reservoir release scheduling).

### Milestone 4: Deployment & Publication
- **Automated data ingestion:** Connect the pipeline to IMD's real-time API or NASA GPM (Global Precipitation Measurement) satellite feeds for live data.
- **Cloud deployment:** Containerize the pipeline and dashboard with Docker; deploy to a public hosting platform (Vercel / AWS / GCP) with a public URL for demonstration.
- **Academic publication:** Format the combined Phase 1 + Phase 2 results for submission to a peer-reviewed journal (target venues: *Chaos*, *Nonlinear Processes in Geophysics*, *Scientific Reports*, or *Journal of Hydrology*).

---

## 7. Repository Structure

```
btpproject/
├── config.yaml                 # All parameters (no magic numbers in code)
├── run_pipeline.ps1            # One-click PowerShell pipeline orchestrator
├── Makefile                    # Make targets for each stage
├── conftest.py                 # pytest sys.path injection
│
├── pipeline/                   # Data processing stages
│   ├── 01_download_data.py
│   ├── 02_build_grid.py
│   ├── 03_extract_events.py
│   ├── 04_sync_matrix.py
│   ├── 05_build_network.py
│   ├── 06_robustness_study.py
│   ├── 07_landslide_validation.py
│   └── 08_export_ui.py
│
├── src/ktnet/                  # Core Python modules
│   ├── io.py                   # File loading, config parsing
│   ├── grid.py                 # Grid construction, basin join
│   ├── events.py               # Extreme event extraction
│   ├── sync.py                 # Event synchronization (Numba)
│   ├── network.py              # Graph construction, centralities
│   ├── robustness.py           # Robustness, basin impact, sensitivity
│   ├── landslide.py            # Landslide validation, bootstrap
│   └── export.py               # Contract file serialization
│
├── tests/                      # 12-test pytest suite
│
├── data/
│   ├── raw/                    # Downloaded source data
│   ├── interim/                # cells.parquet, events.npz, es_matrix.npy
│   └── processed/              # network.graphml, metrics, robustness, etc.
│
├── web/                        # React + Vite dashboard
│   ├── public/data/            # JSON/GeoJSON contract files (UI reads these)
│   ├── src/
│   │   ├── components/         # MapView, Navbar, Sidebar, StatCard, etc.
│   │   ├── pages/              # Overview, NetworkExplorer, Robustness, Basins, Landslide, Method
│   │   ├── state/              # AppContext (global state management)
│   │   ├── lib/                # dataLoader, colors
│   │   ├── types/              # TypeScript interfaces (contract.ts)
│   │   └── styles/             # Tailwind CSS
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── generate_report.py          # Automated BTP Word report compiler
├── screenshots/                # UI screenshots for the Word report
│
├── APPROACH.md                 # High-level approach overview
├── PROJECT_REPORT.md           # Full project report
├── BTP_TWO_PHASE_PLAN.md       # Two-phase BTP execution plan
├── BTP_COMPLETE_REPORT.md      # THIS FILE — comprehensive combined report
├── RUN_INSTRUCTIONS.md         # Step-by-step run guide
├── README.md                   # General project README
└── AGENTS.md                   # Coding agent rules
```

---

## 8. How To Run The Application

### Prerequisites
- **Python 3.12** with scientific packages (numpy, pandas, networkx, numba, scipy, shapely).
- **Node.js v24+** and npm.

### Run the Data Pipeline (if rebuilding from raw data)
```powershell
cd "C:\Users\Ashmi_SN\Desktop\btpproject"
powershell -File run_pipeline.ps1
```

### Launch the Interactive Dashboard
```powershell
# Ensure Node is on PATH
$env:PATH = "C:\Program Files\nodejs;" + $env:PATH

# Install dependencies (one time only)
cd "C:\Users\Ashmi_SN\Desktop\btpproject\web"
npm install

# Start the development server
npm run dev
# Opens http://localhost:3000 in your browser
```

### Run the Test Suite
```powershell
cd "C:\Users\Ashmi_SN\Desktop\btpproject"
python -m pytest tests/ -v
```

### Generate the BTP Word Report
```powershell
pip install python-docx
python generate_report.py
# Produces BTP_Report.docx in the project root
```

---

*Phase 1 completed and documented. Phase 2 research roadmap defined. Ready for term evaluation.*
