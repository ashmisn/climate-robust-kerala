# Kerala Climate Network — Vyuham (Complex System & Network)

<p align="center">
  <img src="web/public/logo.png" alt="Vyuham Logo" width="220" />
</p>

An empirical complex systems and climate network analysis framework investigating extreme monsoon rainfall synchronization over Kerala (+ Western Ghats buffer) across the 1991–2020 climatological normal.

The repository encompasses two scientific investigations and an interactive zero-backend React dashboard:
- **Study A — Basin Robustness:** Percolation breakdown analysis identifying which spatial grid cells and river basins are structurally critical for interstate and regional rainfall teleconnections.
- **Study B — Landslide Validation:** Spatial regression and rank correlation assessing whether complex network centralities correlate with empirical landslide densities from the catastrophic 2018 Kerala monsoon disaster (after controlling for topographic slope).

---

## 1. Architecture

```
IMD 0.25° Daily Rainfall ─┐
India-WRIS River Basins ──┤
SRTM 30m DEM Slope ───────┼─► Python Pipeline ─► web/public/data/*.json ─► Static React Dashboard
2018 Landslide Inventory ─┘
```

**Design Principle:** The Python pipeline processes raw spatial data, calculates Event Synchronization (Quian Quiroga et al. 2002) in `numba`, conducts robustness simulations, and serializes static JSON/GeoJSON files directly into `web/public/data/`. The React + Vite web dashboard is completely static, with no backend server required.

---

## 2. Repository Layout

```
kerala-climate-network/
├── AGENTS.md                 # Rules for coding agents (per Section 9)
├── README.md                 # Project documentation
├── Makefile                  # make data | grid | events | es | network | robustness | landslide | export | all
├── run_pipeline.ps1          # Windows PowerShell pipeline orchestrator
├── config.yaml               # Centralized parameters (bbox, percentiles, seeds, paths)
├── requirements.txt          # Python scientific dependencies
├── conftest.py               # Pytest path configuration
├── data/
│   ├── raw/                  # Acquired raw datasets + PROVENANCE.md
│   ├── interim/              # cells.parquet, events.npz, es_matrix.npy
│   └── processed/            # network.graphml, metrics.parquet, robustness.parquet, landslide_stats.parquet
├── src/ktnet/
│   ├── io.py                 # Loaders for IMD, shapefiles, DEM slope, and landslide inventory
│   ├── grid.py               # 0.25° regular grid construction, land filtering, basin spatial join
│   ├── events.py             # JJAS wet-day extreme precipitation thresholding (90/95/97th percentiles)
│   ├── sync.py               # Event Synchronization in numba (dynamic lag delay, symmetric Q_ij)
│   ├── network.py            # Top 5% thresholding, degree, betweenness, clustering, eigenvector
│   ├── robustness.py         # Study A: Random/degree/betweenness node removal, basin impact ranking
│   ├── landslide.py          # Study B: Landslide density mapping, DEM slope, bootstrap Spearman CI
│   └── export.py             # Serializes static data contract to web/public/data/
├── pipeline/
│   ├── 01_download_data.py   # Stage 1: Data acquisition
│   ├── 02_build_grid.py      # Stage 2: Grid and basin assignment
│   ├── 03_extract_events.py  # Stage 3: Extreme event extraction
│   ├── 04_sync_matrix.py     # Stage 4: Event synchronization matrix
│   ├── 05_build_network.py   # Stage 5: Climate network & centralities
│   ├── 06_robustness_study.py# Stage 6: Study A robustness simulations
│   ├── 07_landslide_validation.py # Stage 7: Study B landslide validation
│   └── 08_export_ui.py       # Stage 8: UI data contract export
├── tests/                    # 12 unit and statistical tests
└── web/                      # React + Vite + TypeScript + Tailwind CSS dashboard
    ├── public/
    │   ├── logo.png          # Project emblem
    │   └── data/             # Exported static contract JSON/GeoJSON files
    └── src/
        ├── types/            # TypeScript interfaces strictly matching Section 4
        ├── lib/              # Async loaders, viridis/magma color ramps
        ├── state/            # AppContext filter and selection state
        ├── components/       # Navbar, Sidebar, MapView (Leaflet), StatCard, DetailDrawer
        └── pages/            # Overview, Network, Robustness, Basins, Landslide, Method
```

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.10+ (with packages: `pip install -r requirements.txt`)
- Node.js LTS (for building and serving the web dashboard)

### Running the Python Scientific Pipeline

To execute all 8 pipeline stages from scratch:
```powershell
# On Windows PowerShell:
.\run_pipeline.ps1 all

# Or using GNU Make:
make all
```

To run a specific pipeline stage:
```powershell
.\run_pipeline.ps1 es          # Runs Stage 4 Event Synchronization
.\run_pipeline.ps1 robustness  # Runs Stage 6 Robustness Study
.\run_pipeline.ps1 test        # Runs test suite (12 tests)
```

### Running Automated Tests
```powershell
python -m pytest tests/ -v
```
Verifies:
- ES matrix symmetry ($Q_{ij} = Q_{ji}$) and normalized bounds $Q \in [0, 1]$
- Extreme event rate matches wet-day percentile expectation (~5%)
- Graph node count and link density (top 5% of possible links)
- Monotonic degradation curves starting at 1.0
- All 9 exported data files conform to the Section 4 Data Contract schema

### Launching the Interactive Web Dashboard

Once the pipeline exports data to `web/public/data/`:
```bash
cd web
npm install
npm run dev
```
Open your browser at `http://localhost:3000`.

To build the static distribution for GitHub Pages or Netlify:
```bash
cd web
npm run build
```
The output in `web/dist/` is 100% static and requires no backend server.

---

## 4. Scientific Limitations (Section 10)

1. **Gauge Interpolation:** IMD 0.25° grid values are interpolated from gauge networks, not physical in-situ weather stations. Results indicate regional precipitation synchronization patterns rather than local rain gauge properties.
2. **Spatial Resolution & Buffer:** At 0.25° (~27 km), the state of Kerala contains ~50 cells; the Western Ghats buffer is what provides sufficient topological size for network analysis. Basin boundaries are approximate.
3. **Geomorphic Confounders:** Landslide occurrence is governed by slope steepness, lithology, soil saturation, and land-cover. Study B is exploratory, and moderate correlations are expected and scientifically valid.
4. **Structural vs Inundation Physics:** Removal simulations quantify structural connectivity within the climate network graph, not direct hydrological flood routing.
5. **Parameter Sensitivity:** Findings depend on chosen event thresholds and link densities; multi-threshold sensitivity analysis (90, 95, 97th percentiles) quantifies this variance.
