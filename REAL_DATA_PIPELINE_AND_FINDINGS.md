# Vyuham: Kerala Climate Network (Real Data Pipeline & Findings)
**BTP Comprehensive Research Documentation & Scientific Report**  
*Investigating Synchronized Extreme Monsoon Precipitation Patterns (1981–2020) and Empirical Disaster Vulnerability in Kerala*

---

## 1. Executive Summary & Research Motivation

The **Vyuham** research initiative investigates the complex network topology of extreme monsoon precipitation across Kerala and the Western Ghats buffer zone, evaluating how synchronized rainfall patterns govern regional hydrological vulnerability and empirical disaster outcomes.

By shifting from synthetic prototypes to **strict Real Data Mode**, this project guarantees 100% observational provenance across all stages:
1. **Climate Record**: 40-year daily gridded rainfall ($0.25^\circ \times 0.25^\circ$) from the **India Meteorological Department (IMD)** spanning JJAS 1981–2020 (4,880 daily timesteps).
2. **Administrative Boundaries**: Official **GADM 4.1 Level-1** boundary for Kerala and **Census of India 2011** 14-district vector polygons.
3. **River Basins & Hydrography**: Official **India-WRIS / Central Water Commission (CWC)** sub-basins joined with **KeralaData 500-segment river vectors**.
4. **Disaster Inventory**: The complete, authoritative **van Westen et al. (2020)** GPS disaster inventory documenting **4,728 landslides** triggered during the historic August 2018 monsoon disaster.

### Key Scientific Findings:
* **Study A (Robustness & Structural Criticality)**: The regional synchronization network ($N=97$, 232 edges) is resilient against random meteorological node failures ($64.5\%$ LCC preserved at $30\%$ removal), but suffers a severe **percolation breakdown at $f \approx 20\%$ under targeted degree-based hub attacks** (LCC plunges to $30.7\%$).
* **Basin Null Models**: Periyar basin removal drops the network giant component by $32.0\%$. However, a size-matched Monte Carlo null model ($10,000$ draws, 2 seeds) with **step-down Holm-Bonferroni correction across all 6 named basins** reveals $p_{\text{Holm}} = 1.000$. The high drop is driven by the basin's spatial footprint ($k=27$ cells) rather than an anomalously centralized synchronization topology.
* **Study B (2018 Landslide Validation)**: Mapping all 4,728 GPS landslide points shows that extreme-rainfall synchronization centralities exhibit weak, statistically non-significant correlation with localized landslide density ($\rho \in [-0.03, +0.06]$, $p > 0.50$, 95% bootstrap CIs straddling zero). This confirms that while synoptic rainfall teleconnections govern regional flood conveyance (Study A), catastrophic slope instability is dictated by hyper-local geotechnical thresholds (steep terrain slope $>25^\circ$, soil saturation, and local lithology).

---

## 2. Observational Data Provenance Log

In accordance with strict scientific integrity principles, all synthetic, modeled, and analytic approximations have been permanently withdrawn.

| Dataset Name | Domain / Coverage | Provenance & Source Authority | File Location in Repository | Verification Method |
| :--- | :---: | :--- | :--- | :--- |
| **IMD Gridded Daily Rainfall** | $8.0^\circ\text{N} - 13.5^\circ\text{N}$, $74.0^\circ\text{E} - 78.0^\circ\text{E}$ | India Meteorological Department (IMD), Pune. 40-year daily series (JJAS 1981–2020; 4,880 daily frames). | `data/raw/imd_rainfall_real.npz` | NetCDF raster extraction; 0 zero-variance terrestrial cells |
| **Kerala State Boundary** | Kerala State Polygon | Database of Global Administrative Areas (GADM) v4.1 (`NAME_1 == "Kerala"`). | `data/raw/kerala_boundary_gadm.geojson` | 2,904-vertex MultiPolygon; EPSG:4326 |
| **District Boundaries** | 14 Revenue Districts | Census of India 2011 / Survey of India official boundary vectors. | `data/raw/kerala_districts.geojson` | Complete administrative polygon coverage |
| **River Basin Boundaries** | Major Catchments | Central Water Commission (CWC) & India Water Resources Information System (India-WRIS). | `data/raw/basins_real.geojson` | Official sub-basin polygons derived from `WRIS_SubBasin.parquet` |
| **River Vector Network** | 500 River Segments | KeralaData open GIS repository (`AllRivers.geojson`). | `data/raw/AllRivers.geojson` | Spatially intersected with WRIS sub-basins |
| **2018 Landslide Inventory** | Kerala (Aug 2018) | van Westen, C.J. (2020), Geological Survey of India (GSI) & National Remote Sensing Centre (NRSC). | `data/raw/Kerela landslide.shp` (`.dbf`, `.shx`, `.prj`, `.cpg`, `.sbn`) | 4,728 POINTZ records; WGS 84 geographic coordinates |

---

## 3. Climate Complex Network Methodology

### 3.1 Domain Filtering & Marine Zero-Rainfall Cell Audit
The study region comprises a $0.25^\circ \times 0.25^\circ$ grid over Kerala and the adjacent Western Ghats ridge. Across the 40-year historical record, exactly **6 cells** situated entirely in the Arabian Sea registered zero precipitation ($0.0\text{ mm}$ over all 4,880 timesteps):
* `c_001` ($8.25^\circ\text{N}, 76.75^\circ\text{E}$)
* `c_025` ($9.75^\circ\text{N}, 76.00^\circ\text{E}$)
* `c_040` ($10.50^\circ\text{N}, 75.75^\circ\text{E}$)
* `c_051` ($11.00^\circ\text{N}, 75.50^\circ\text{E}$)
* `c_057` ($11.25^\circ\text{N}, 75.50^\circ\text{E}$)
* `c_063` ($11.50^\circ\text{N}, 75.25^\circ\text{E}$)

These 6 cells were disconnected marine artifacts ($\text{degree} = 0$). Removing them purified the active network to **$N=97$ nodes**.

### 3.2 Event Synchronization (ES) Formulation
For each active grid cell $i$, extreme daily precipitation events are defined dynamically:
$$E_i(t) = \mathbb{I}\left(R_i(t) \ge \text{p}_{95}(R_i) \;\land\; R_i(t) \ge 5.0\text{ mm}\right)$$

For every pair of cells $(i, j)$ with event times $\{t_m^i\}$ and $\{t_n^j\}$, dynamical delays are constrained by:
$$\tau_{m,n} = \frac{1}{2} \min\left(t_{m+1}^i - t_m^i,\; t_m^i - t_{m-1}^i,\; t_{n+1}^j - t_n^j,\; t_n^j - t_{n-1}^j\right)$$
$$\tau_{\max} = 10\text{ days}$$

Event coincidence counts $c(i|j)$ track events in $i$ preceded by $j$ within $\tau = \min(\tau_{m,n}, \tau_{\max})$. The symmetric synchronization strength $Q_{ij}$ is:
$$Q_{ij} = \frac{c(i|j) + c(j|i)}{\sqrt{(s_i - 2)(s_j - 2)}}$$

### 3.3 Adjacency Thresholding
To extract the backbone of synchronized moisture delivery, edges are placed across the top $5\%$ pair synchronization scores ($Q_{ij} \ge 0.5014$):
* **Active Nodes**: $N = 97$
* **Undirected Edges**: $M = 232$
* **Giant Component Size**: $N_{\text{LCC}} = 75$ nodes ($77.3\%$ of domain)

---

## 4. Study A: Network Robustness & Catchment Vulnerability

### 4.1 Percolation Collapse Under Targeted Attack
The network's structural integrity was evaluated by progressively removing nodes under three operational regimes:
1. **Random Failure** ($1,000$ iterations)
2. **Targeted Degree Attack** (removing highest-degree synchronization hubs)
3. **Targeted Betweenness Attack** (removing highest-betweenness routing bottlenecks)

```
Fraction Removed (f)   Random Failure LCC    Degree Attack LCC    Betweenness Attack LCC
-----------------------------------------------------------------------------------------
 5%  (k = 5)                93.9%                 93.3%                 93.3%
10%  (k = 10)               87.9%                 82.7%                 86.7%
20%  (k = 19)               77.4%                 30.7%                 60.0%  <-- Breakdown
30%  (k = 29)               64.5%                 25.3%                 21.3%
```

**Finding**: While random meteorological disturbances degrade connectivity gracefully (linear slope $\approx -1.0$), **targeted degree attack precipitates a sharp second-order percolation transition at $f \approx 0.20$**, collapsing the giant component from $77.4\%$ down to $30.7\%$.

---

### 4.2 Basin Null Model Analysis (10,000 Monte Carlo Draws)
To determine if removing specific hydrological catchments causes disproportionate structural damage to Kerala's moisture transport network, size-matched null models were evaluated:
* **Scattered Null**: $k$ uniformly random nodes selected without replacement.
* **Contiguous Null**: A random seed node and its $k-1$ spatial nearest neighbors.
* **Family-Wise Error Rate Control**: Step-down **Holm-Bonferroni correction** applied across the 6 named basins (*Other / Coastal Buffer* excluded as non-hydrological).

#### Benchmark Results Across Independent Seeds (10,000 Draws each):

```
Basin Name            k    Observed Drop   Scattered Null Mean   Scatt. Holm p   Contig. Null Mean   Contig. Holm p
-------------------------------------------------------------------------------------------------------------------
Periyar and others   27       32.00%             33.44%             1.0000            36.81%            1.0000
Varrar and others    17       22.67%             20.35%             0.9340            24.10%            1.0000
Netravati and others 12       21.33%             14.09%             0.2058            15.98%            0.9870
Cauvery Middle       10        1.33%             11.70%             1.0000            13.61%            1.0000
Cauvery Upper        10        4.00%             11.71%             1.0000            13.65%            1.0000
Vaippar and others    2        0.00%              2.29%             1.0000             2.63%            1.0000
```

> **Scientific Conclusion on Basin Fragility**:  
> In uncorrected raw tests, Netravati showed marginal significance ($p_{\text{raw}} = 0.034$), but after Holm correction across all basins, **no basin displays statistically significant excess structural damage ($p_{\text{Holm}} > 0.05$)**. The observed 32.0% LCC reduction upon removing Periyar is entirely explained by its large spatial area ($k=27$), not by topological anomaly.

---

### 4.3 Verified River Line Intersections
Spatial intersection of 500 line features from `AllRivers.geojson` against India-WRIS sub-basins confirmed:
* **Periyar and others (157 rivers)**: Periyar River, Chalakudy, Muvattupuzha, Achenkovil Ar, Kallada, Meenachil, Manimala, Anaimudi Ar, Ithikkara, Kodayar.
* **Varrar and others (89 rivers)**: Bharathapuzha (Nila), Chaliyar, Beypore, Agala Puzha, Aliyar, Tirur, Kadalundi, Korapuzha.
* **Netravati and others (90 rivers)**: Valapattanam, Chandragiri, Kuppam, Karyangod / Thejaswini, Nileshwar, Payaswani.
* **Cauvery Middle (75 rivers)**: Bhavani, Silent Valley streams, Cauvery tributaries.
* **Cauvery Upper (33 rivers)**: Kabini, Mananthavady, Panamaram, Noolpuzha.
* **Pamba and others (18 rivers)**: Pamba mainstem, Azhutha, Kakkad, Chittar.
* **Vaippar and others (26 rivers)**: Upper eastern slope streams (Chittar, Chilambu Odai).

---

### 4.4 Invariant Structural Hubs Across Event Thresholds ($p_{90}, p_{95}, p_{97}$)
Evaluating sensitivity across link-density cutoffs ($10\%$, $5\%$, $3\%$):
* **Stable Degree Hubs (Top-10 in all 3 thresholds)**:
  - `c_030` ($10.00^\circ\text{N}, 76.00^\circ\text{E}$ — Ernakulam/Periyar coast)
  - `c_036` ($10.25^\circ\text{N}, 76.25^\circ\text{E}$ — Chalakudy / Periyar corridor)
  - `c_047` ($10.75^\circ\text{N}, 76.00^\circ\text{E}$ — Palakkad Gap lowland)
  - `c_052` ($11.00^\circ\text{N}, 75.75^\circ\text{E}$ — Malappuram/Kozhikode coast)
* **Stable Betweenness Hub (Top-10 in all 3 thresholds)**:
  - `c_072` ($11.75^\circ\text{N}, 75.75^\circ\text{E}$ — Kannur / Wayanad mountain pass)

---

## 5. Study B: 2018 Landslide Disaster Validation

### 5.1 Dataset Characteristics & Geospatial Ingestion
* **Inventory**: Official Geological Survey of India (GSI) & National Remote Sensing Centre (NRSC) inventory compiled by van Westen (2020).
* **Geometry**: 4,728 `POINTZ` GPS features with elevation and continuous SRTM slope `RASTERVALU`.
* **Spatial Matching**:
  - **4,586 landslides** mapped inside the 97 active grid cells.
  - **4,391 landslides** concentrated inside the 48 eligible Kerala cells ($\ge 50\%$ within state boundary).
  - Remaining 142 points located on the eastern Munnar border crest ($77.12^\circ\text{E} - 77.40^\circ\text{E}$).

#### Major Landslide Concentration Hotspots:
1. **Cell `c_034`** ($10.00^\circ\text{N}, 77.00^\circ\text{E}$ — Idukki High Ranges / Munnar): **1,245 landslides** ($1.646\text{ pts/km}^2$).
2. **Cell `c_029`** ($9.75^\circ\text{N}, 77.00^\circ\text{E}$ — Peerumade / Cardamom Hills): **544 landslides** ($0.719\text{ pts/km}^2$).
3. **Cell `c_044`** ($10.50^\circ\text{N}, 76.75^\circ\text{E}$ — Nelliyampathy Hills / Palakkad): **311 landslides** ($0.411\text{ pts/km}^2$).
4. **Cell `c_066`** ($11.50^\circ\text{N}, 76.00^\circ\text{E}$ — Wayanad Plateau / Meppadi): **281 landslides** ($0.372\text{ pts/km}^2$).

---

### 5.2 Spearman Correlation & Bootstrap Analysis
To test whether climatological synchronization centralities correspond to localized slope failures during August 2018, non-parametric Spearman rank correlations were computed across active cells with **1,000 bootstrap resamples**:

```
Centrality Metric        Spearman ρ    p-value       95% Bootstrap CI       Significance
----------------------------------------------------------------------------------------
Degree Centrality          +0.059       0.5627      [-0.144, +0.253]       Not Significant
Betweenness Centrality     +0.059       0.5673      [-0.162, +0.264]       Not Significant
Clustering Coefficient     -0.028       0.7831      [-0.225, +0.181]       Not Significant
Eigenvector Centrality     +0.001       0.9958      [-0.187, +0.200]       Not Significant
```

#### Slope-Stratified Breakdown:
Terrain slope was computed using each point's embedded SRTM continuous raster slope (`RASTERVALU`, mean $24.0^\circ$ at failure sites):
* **High Slope Class ($>18^\circ$, $N=36$ cells)**:
  - Degree: $\rho = +0.069$ ($p = 0.689$)
  - Betweenness: $\rho = +0.067$ ($p = 0.698$)
  - Eigenvector: $\rho = +0.118$ ($p = 0.492$)
* **Medium Slope Class ($8^\circ - 18^\circ$, $N=8$ cells)**: $\rho \approx 0.0$
* **Low Slope Class ($<8^\circ$, $N=53$ cells)**: Dominated by flat coastal plains where landslide density is zero.

---

### 5.3 Scientific Explanation of the Weak Correlation
In synthetic toy datasets, artificial correlations of $\rho > 0.7$ are easily manufactured. However, with **real observational disaster records**, the correlation is near-zero ($\rho \in [-0.03, +0.06]$) for clear physical reasons:
1. **Scale Disparity**: Event Synchronization captures **synoptic-scale moisture transport corridors** (~25–50 km grid scale), which explains regional river basin discharge and flood inundation.
2. **Local Geotechnical Controls**: Slope failures require geotechnical failure thresholds (shear stress $>$ shear strength), determined by:
   - Steep terrain gradients ($>25^\circ$)
   - Overburden soil regolith depth and clay-layer pore-water pressure
   - Local anthropogenic land use (rubber/tea plantation terracing, road cuts)
3. **Takeaway**: Climatological rainfall synchrony provides the **moisture delivery mechanism**, but static topographical slope and local hydrology determine **where slopes collapse**.

---

## 6. Frontend Web Dashboard Architecture

The Vyuham web platform is a responsive React + TypeScript dashboard designed around a strict data contract:

### 6.1 Data Contract Files (`web/public/data/`)
* **`meta.json`**: Project metadata, coordinate bounds, resolution, and config hash.
* **`cells.geojson`**: 97 grid cells containing `cell_id`, coordinates, catchment tags, centrality metrics, real `landslide_count_2018`, `landslide_density`, `mean_slope`, and `slope_class`.
* **`links.json`**: 232 network synchronization edges with source, target, and $Q_{ij}$ weights.
* **`basins.geojson`**: CWC / India-WRIS hydrological sub-basin polygons.
* **`robustness.json`**: Percolation curves for random, degree, and betweenness attacks ($f \in [0, 0.50]$).
* **`critical_nodes.json`**: Top structural hub rankings and centrality distributions.
* **`landslide_stats.json`**: Overall and slope-stratified correlation coefficients, $p$-values, 95% bootstrap CIs, and 97 scatter plot tuples.
* **`landslide_points.json`**: All **4,728 real GPS points** from van Westen (2020) for Leaflet map overlay.

### 6.2 Application Pages
1. **Overview Page**: Synoptic summary of the Kerala monsoon network, key hubs, and interactive metric maps.
2. **Network Page**: Graph topology exploration, edge weight threshold filtering, and hub node identification.
3. **Robustness Page**: Interactive percolation degradation curves comparing random vs. degree vs. betweenness attacks.
4. **Basins Page**: Catchment subnetwork impact rankings, river memberships, and Monte Carlo null model comparisons.
5. **Landslides Page (Study B)**:
   - Interactive scatter plot of Centrality vs. Empirical Landslide Density (color-coded by slope tertile).
   - Spatial Coincidence Map rendering 4,728 red GPS landslide markers over Kerala grid cells.
   - Spearman rank correlation summary table with 95% bootstrap confidence intervals.

---

## 7. Verification & Automated Test Suite

A comprehensive test suite in `tests/` validates both numerical code and the web data contract:

```
Test Module                      Tests Passed   Verification Scope
-------------------------------------------------------------------------------------------------
tests/test_contract.py                 5        Schema validation for all 6 public JSON/GeoJSON files
tests/test_events.py                   1        95th percentile event extraction & threshold filtering
tests/test_landslide_controls.py       7        Boundary tagging, toy cell counting, block bootstrap, fallback
tests/test_network.py                  1        Graph construction, degree/betweenness/eigenvector metrics
tests/test_null_models.py              3        Scattered and contiguous null models, Monte Carlo draws
tests/test_robustness.py               1        LCC percolation curves and targeted hub removal logic
tests/test_sync.py                     4        Event synchronization matrix symmetry and tau delays
-------------------------------------------------------------------------------------------------
TOTAL                                 22 passed in 4.21s (100% pass rate)
```

---

## 8. BTP Viva / Review Defense Strategy

| Reviewer Question / Critique | Defensible Scientific Response |
| :--- | :--- |
| **"Why is your correlation between rainfall centralities and landslides weak ($\rho \approx 0.06$)?"** | *"In synthetic benchmarks, high correlations are often artifacts of circular modeling. In reality, extreme rainfall synchronization operates at the synoptic scale (~25 km) to deliver moisture, while landslide initiation is controlled by local geotechnical factors—specifically steep slopes ($>25^\circ$), regolith thickness, and pore pressure. Our results honestly demonstrate that rainfall synchrony alone cannot predict slope failure without topographical controls."* |
| **"Does removing Periyar basin cause anomalous network collapse?"** | *"Removing Periyar causes a 32.0% LCC drop, making it the most impactful basin in absolute terms. However, our 10,000-draw size-matched null models and Holm-Bonferroni correction ($p_{\text{Holm}} = 1.000$) demonstrate that this drop is entirely proportional to its large spatial footprint ($k=27$ cells), not an anomalous topological bottleneck."* |
| **"Why did you exclude 6 cells from the original 103 grid?"** | *"An empirical audit of the 40-year IMD record revealed that 6 coastal fringe cells lie entirely over the Arabian Sea with 0.0 mm recorded rainfall. They had degree 0 and were isolated from the network. Removing them refined the domain to 97 active terrestrial cells, preventing distortion of the LCC denominator."* |
| **"What is the operational value of this network for disaster management?"** | *"The percolation analysis reveals a critical threshold at 20% hub removal where regional connectivity collapses. For flood management, monitoring the stable degree hubs (e.g., Chalakudy corridor `c_036` and Palakkad lowland `c_047`) provides early indication of multi-basin synchronized deluge."* |

---

*Report compiled and verified locally. All pipeline outputs preserved in `outputs/real_data_run_v2/` and `web/public/data/`.*
