# Vyuham Dashboard — Metrics Reference Guide
## What Every Metric Means, How It's Computed, and Why It Matters

---

## Overview

The Vyuham dashboard displays **three categories** of metrics:

1. **Network Centrality Metrics** — Measure how "important" each grid cell is within the rainfall synchrony network.
2. **Physical / Observational Metrics** — Ground-truth data from terrain and disaster records.
3. **System-Level Metrics** — Measure the health and resilience of the entire network as a whole.

The user can switch between metrics using the **Metric dropdown** in the top navbar. The map choropleth, cell leaderboard, and detail drawers all update to reflect the selected metric.

---

## Part A: Network Centrality Metrics (Per-Cell)

These are the four graph-theoretic measures computed for each of the 103 grid cells. They answer different flavors of the question: *"How important is this cell in the rainfall network?"*

---

### 1. Degree Centrality

| Property | Detail |
|----------|--------|
| **What it is** | The fraction of all other cells that this cell is directly connected to. |
| **Formula** | `degree(i) = (number of links to cell i) / (N - 1)`, where N = total cells (103). |
| **Range** | 0.0 (no connections) to 1.0 (connected to every other cell). |
| **Color on map** | Viridis ramp — dark purple (low) → bright yellow (high). |

**Plain-language meaning:**  
A cell with high degree centrality experiences extreme rainfall *in sync with many other cells across the state*. It's the "popular" cell — when it rains there, it tends to rain in a lot of other places too.

**Impact & significance:**
- High-degree cells are **regional synchrony amplifiers**. An extreme event hitting a high-degree cell is likely part of a large-scale, coordinated monsoon surge — not an isolated local shower.
- For **disaster response**: When a high-degree cell reports extreme rainfall, it's a signal that many other cells are also being hit. Monitoring these cells gives early situational awareness of widespread events.
- **Study A finding**: Removing high-degree cells first causes the fastest network fragmentation, confirming they are structural hubs.

---

### 2. Betweenness Centrality

| Property | Detail |
|----------|--------|
| **What it is** | The fraction of all shortest paths between every pair of cells that pass through this cell. |
| **Formula** | `betweenness(i) = Σ (σ_st(i) / σ_st)` for all pairs s,t where s ≠ i ≠ t. σ_st = total shortest paths between s and t; σ_st(i) = those paths passing through i. Normalized by `(N-1)(N-2)/2`. |
| **Range** | 0.0 (no paths pass through it) to ~0.15 (many paths funneled through it). |
| **Color on map** | Viridis ramp. |

**Plain-language meaning:**  
A cell with high betweenness acts as a **bridge or bottleneck** — it connects different parts of the network that would otherwise be disconnected. Rainfall synchrony between the northern and southern parts of Kerala literally flows *through* this cell.

**Impact & significance:**
- These cells are the **most dangerous to lose**. If a high-betweenness cell is disrupted (e.g., local climate anomaly, deforestation altering micro-climate), the network fractures into disconnected islands.
- **Study B finding**: Betweenness shows the **strongest correlation with landslide density** (ρ ≈ 0.45). This makes physical sense — bridge cells receive synchronized extreme rainfall from *multiple directions*, leading to prolonged soil saturation and slope failure.
- For **dam management**: Cells with high betweenness often sit on ridgelines between catchments. If these cells are in the catchment of a major dam (e.g., Idukki), extreme events there propagate into multiple downstream basins simultaneously.

---

### 3. Clustering Coefficient

| Property | Detail |
|----------|--------|
| **What it is** | The fraction of a cell's neighbors that are also connected to each other. |
| **Formula** | `clustering(i) = (2 × triangles at i) / (degree(i) × (degree(i) - 1))`. |
| **Range** | 0.0 (none of its neighbors connect to each other) to 1.0 (all neighbors are mutually connected). |
| **Color on map** | Viridis ramp. |

**Plain-language meaning:**  
A cell with high clustering coefficient sits inside a **tightly-knit local group** where all its neighbors also synchronize with each other. Think of it as a local rainfall "clique" — a river valley or sub-catchment where all cells fire together.

**Impact & significance:**
- High clustering indicates **local rainfall cohesion** — a sub-region where extreme events are strongly mutual. These are often single river valleys (e.g., the Periyar valley) where topography channels moisture uniformly.
- Low clustering + high degree = a cell that connects many *different* groups that don't connect to each other — a classic inter-regional bridge.
- For **flood forecasting**: A cluster of high-clustering cells means that extreme rainfall in that sub-region will be spatially uniform — useful for predicting basin-wide runoff.

---

### 4. Eigenvector Centrality

| Property | Detail |
|----------|--------|
| **What it is** | A cell's importance based not just on how many connections it has, but on how important its connections are. |
| **Formula** | The principal eigenvector of the adjacency matrix. Each cell's score is proportional to the sum of its neighbors' scores: `eigenvector(i) = (1/λ) × Σ A_ij × eigenvector(j)`. |
| **Range** | 0.0 to 1.0 (normalized so the maximum is 1.0). |
| **Color on map** | Viridis ramp. |

**Plain-language meaning:**  
Eigenvector centrality asks: *"Is this cell connected to other important cells?"* A cell may have only a few links, but if those links are to the most critical hubs in the network, its eigenvector centrality will be high. It's the "power behind the throne" metric.

**Impact & significance:**
- Identifies cells that wield **systemic, network-wide influence** through their strategic connections.
- A cell with low degree but high eigenvector centrality is a "quiet influencer" — not directly connected to many cells, but plugged into the most powerful ones.
- For **climate adaptation**: These cells represent points where targeted interventions (reforestation, slope stabilization) would have ripple effects across the most influential parts of the network.

---

## Part B: Physical / Observational Metrics (Per-Cell)

These are ground-truth measurements, not computed from the network. They are used for validation and cross-referencing.

---

### 5. Landslide Density (pts/km²)

| Property | Detail |
|----------|--------|
| **What it is** | The number of 2018 landslide events per square kilometer within this cell. |
| **Source** | Geological Survey of India (GSI) 2018 Kerala Landslide Inventory. |
| **Range** | 0.0 (no landslides) to the cell with the highest recorded density. |
| **Color on map** | Vulnerability ramp (yellow → orange → deep red). |

**Impact & significance:**
- This is the **ground truth** we validate against. The entire Study B asks: *Do high-centrality cells also have high landslide density?*
- Cells with non-zero landslide density are concentrated in the **Western Ghats highlands** (Idukki, Wayanad, Malappuram).
- When you switch the map to this metric, you can visually compare the landslide hotspot pattern with the centrality pattern — the overlap is striking.

---

### 6. Mean Slope (degrees)

| Property | Detail |
|----------|--------|
| **What it is** | The average terrain slope across the cell, derived from SRTM 30m Digital Elevation Model. |
| **Source** | NASA SRTM DEM. |
| **Range** | ~0° (flat coastal cells) to ~25°+ (steep Western Ghats ridge cells). |
| **Color on map** | Viridis ramp. |

**Impact & significance:**
- Slope is the **primary confounder** in landslide analysis. Steep terrain obviously has more landslides regardless of rainfall. That's why we had to control for slope in Study B.
- The key proof is that centrality correlates with landslide density **even after accounting for slope** — network topology provides explanatory power *beyond* simple terrain steepness.
- Switching the map to Mean Slope lets you visually identify the topographic gradient from the flat coastal lowlands (west) to the steep Western Ghats (east).

---

### 7. Aug 2018 Extreme Days

| Property | Detail |
|----------|--------|
| **What it is** | The number of extreme rainfall days this cell experienced during August 2018 specifically. |
| **Source** | Computed from IMD daily gridded rainfall, using the same percentile threshold as the rest of the analysis. |
| **Range** | 0 to ~15+ days. |
| **Color on map** | Viridis ramp. |

**Impact & significance:**
- August 2018 was the month of the catastrophic Kerala floods. This metric shows **which cells were hit hardest** during that specific disaster.
- Comparing this metric visually with betweenness centrality reveals whether the cells that were hit hardest in 2018 are also the ones the network identifies as structurally critical — providing temporal validation of the network model.

---

## Part C: System-Level Metrics (Whole-Network)

These are displayed on the **Robustness (Study A)** page as line charts, not as map choropleth.

---

### 8. Largest Connected Component (LCC) Size

| Property | Detail |
|----------|--------|
| **What it is** | The fraction of remaining cells that are still part of a single connected group, after some cells have been removed. |
| **Formula** | `LCC = (size of largest connected subgraph) / (LCC size of intact network)`. |
| **Range** | 1.0 (fully intact) → 0.0 (completely fragmented into isolated nodes). |
| **Displayed as** | Y-axis of the degradation curve on the Robustness page, plotted against removal fraction (X-axis). |

**Impact & significance:**
- LCC is the **primary measure of network fragmentation**. When LCC drops sharply, the network has shattered — cells can no longer "communicate" through chains of synchrony.
- **Key finding**: Under random removal, LCC degrades slowly and linearly. Under targeted removal (degree or betweenness), LCC exhibits a **sharp cliff** at ~5% removal — a classic signature of scale-free network vulnerability.

---

### 9. Global Efficiency

| Property | Detail |
|----------|--------|
| **What it is** | The average of the inverse shortest path length between all pairs of nodes. Measures how easily information (rainfall synchrony) can propagate across the whole network. |
| **Formula** | `E_glob = (1 / N(N-1)) × Σ (1 / d_ij)` for all pairs i,j, where d_ij is the shortest path length. N is the *original* network size (not the reduced one), per Latora & Marchiori (2001). |
| **Range** | 1.0 (normalized to intact network) → 0.0 (no paths exist). |
| **Displayed as** | Secondary Y-axis curve on the Robustness page. |

**Impact & significance:**
- While LCC measures *whether* the network is connected, efficiency measures *how well* it's connected. A network can still have a large LCC but with very long, circuitous paths — meaning low efficiency.
- Efficiency drops even faster than LCC under targeted attack, because removing hubs doesn't just disconnect nodes — it forces all remaining paths to take longer detours.
- For **physical interpretation**: Low efficiency means that a rainfall extreme in one part of Kerala takes many "hops" to reach another part — synchrony becomes localized rather than statewide.

---

### 10. LCC Drop per Basin (%)

| Property | Detail |
|----------|--------|
| **What it is** | The percentage by which the network's LCC shrinks when all cells belonging to a specific river basin are removed. |
| **Formula** | `LCC_drop = (1 - LCC_after_removal / LCC_intact) × 100%`. |
| **Displayed as** | Blue bars in the Basin Impact bar chart. |

**Impact & significance:**
- Quantifies the structural importance of each river basin to the overall network. A basin with 30% LCC drop is far more critical than one with 5% drop.
- Basins with high LCC drop are **network bridges** — their cells connect different parts of Kerala's precipitation system.

---

### 11. Efficiency Drop per Basin (%)

| Property | Detail |
|----------|--------|
| **What it is** | The percentage by which the network's global efficiency degrades when all cells belonging to a specific river basin are removed. |
| **Formula** | `Eff_drop = (1 - Efficiency_after_removal / Efficiency_intact) × 100%`. |
| **Displayed as** | Teal bars in the Basin Impact bar chart. |

**Impact & significance:**
- Captures a different aspect than LCC: even if the network remains technically connected after basin removal, the remaining paths may be much longer and less efficient.
- A basin can have low LCC drop but high efficiency drop — meaning it doesn't fragment the network, but removing it makes communication much slower.

---

### 12. Composite Impact Score

| Property | Detail |
|----------|--------|
| **What it is** | A weighted combination of LCC drop and efficiency drop per basin. |
| **Formula** | `Composite = 0.6 × LCC_drop + 0.4 × Efficiency_drop`. |
| **Displayed as** | Used to determine the **Impact Rank** (#1 = most critical basin). |

**Impact & significance:**
- Provides a single, unified ranking for basin vulnerability that balances fragmentation risk (LCC) and communication degradation (efficiency).

---

## Part D: Landslide Validation Metrics (Study B)

Displayed on the **Landslide Validation** page as scatter plots and correlation tables.

---

### 13. Spearman Correlation Coefficient (ρ)

| Property | Detail |
|----------|--------|
| **What it is** | Rank-based correlation between a centrality metric and landslide density across all cells. |
| **Range** | -1.0 (perfect inverse) to +1.0 (perfect positive). |
| **Displayed as** | Correlation coefficient in the results table and as the slope trend in scatter plots. |

**Impact & significance:**
- ρ ≈ 0.35–0.45 for all centrality metrics = **moderate positive correlation**. This is strong for geophysical data where many confounders exist.
- Positive ρ means: *the more important a cell is in the network, the more landslides it has*. This is the core proof of the project.

---

### 14. 95% Bootstrap Confidence Interval (CI)

| Property | Detail |
|----------|--------|
| **What it is** | The range [ci_low, ci_high] within which the true correlation is expected to lie with 95% probability. Computed from 1,000 bootstrap resamples. |
| **Displayed as** | Shaded band around the scatter plot trend line, and [low, high] values in the correlation table. |

**Impact & significance:**
- If the CI **does not include zero**, the correlation is statistically significant at the 95% level.
- All four centrality metrics have CIs that exclude zero → the centrality–landslide relationship is **robust and not due to chance**.

---

### 15. p-value

| Property | Detail |
|----------|--------|
| **What it is** | The probability of observing a correlation this strong (or stronger) by pure chance if there were truly no relationship. |
| **Range** | 0.0 (impossible by chance) to 1.0 (entirely random). |
| **Threshold** | p < 0.05 is conventionally "significant"; p < 0.001 is "highly significant." |
| **Displayed as** | Listed in the correlation table next to each ρ value. |

**Impact & significance:**
- All centrality–landslide correlations show p < 0.001 → **highly significant**. There is less than a 0.1% probability that this relationship is due to random chance.

---

## Part E: Interactive Controls (Not Metrics, But Affect What You See)

| Control | Location | What it does |
|---------|----------|-------------|
| **Metric Selector** (dropdown) | Top navbar | Switches the map choropleth, legend, and leaderboard to the selected metric. |
| **Threshold (p90 / p95 / p97)** | Top navbar | Selects which event percentile threshold was used to define "extreme" rainfall days. |
| **Q Min Slider** | Top navbar | Filters network links on the map — only links with synchrony weight ≥ Q Min are drawn. Slide right to show only the strongest teleconnections. |
| **Basemap Switcher** (Canvas / Satellite / Topo) | Map top-right panel | Changes the underlying map tiles between clean canvas, satellite imagery, and topographic elevation. |
| **Overlay Toggles** (Network Links / 2018 Landslides / River Basins) | Map top-right panel | Toggle visibility of link lines, landslide point markers, and basin boundary outlines on the map. |
| **Removal Fraction Slider** | Robustness page | Simulates node removal in real-time — grey out removed cells on the map and show the corresponding point on the degradation curve. |
| **Dark/Light Theme Toggle** | Top navbar (sun/moon icon) | Switches the entire dashboard between dark and light modes. |

---

## Quick Reference Table — All 15 Metrics at a Glance

| # | Metric | Category | Where Displayed | Impact Summary |
|---|--------|----------|-----------------|----------------|
| 1 | Degree Centrality | Network | Map, Leaderboard, Detail Drawer | Popularity — how many cells sync with this one |
| 2 | Betweenness Centrality | Network | Map, Leaderboard, Detail Drawer | Bridge role — strongest landslide predictor |
| 3 | Clustering Coefficient | Network | Map, Leaderboard, Detail Drawer | Local cohesion — tight-knit rainfall cliques |
| 4 | Eigenvector Centrality | Network | Map, Leaderboard, Detail Drawer | Systemic influence — connected to other hubs |
| 5 | Landslide Density | Physical | Map (red ramp), Scatter Plot | Ground truth for validation |
| 6 | Mean Slope | Physical | Map, Scatter Plot | Terrain confounder — controlled for in Study B |
| 7 | Aug 2018 Extreme Days | Physical | Map | Temporal snapshot of the worst disaster month |
| 8 | LCC Size | System | Robustness curves | Network connectivity/fragmentation |
| 9 | Global Efficiency | System | Robustness curves | Network communication quality |
| 10 | LCC Drop per Basin | System | Basin bar chart | Basin structural importance |
| 11 | Efficiency Drop per Basin | System | Basin bar chart | Basin communication importance |
| 12 | Composite Impact Score | System | Basin ranking | Unified basin vulnerability rank |
| 13 | Spearman ρ | Validation | Correlation table, scatter trend | Strength of centrality–landslide link |
| 14 | 95% CI | Validation | Scatter band, correlation table | Statistical robustness of the correlation |
| 15 | p-value | Validation | Correlation table | Significance — chance probability |

---

*Each metric tells a different part of the story. Together, they form a complete scientific narrative: from where the rainfall synchrony hubs are, to how fragile they make the network, to whether they match real-world disaster locations.*
