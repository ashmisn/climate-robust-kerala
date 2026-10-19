# Phase 1 Strengthening v3: Independent Terrain & Study B Validation
*Comprehensive Scientific Report with Full Observational Provenance*

## Step 0: Slope Circularity Audit
- **Verdict**: NOT independent (circular)
- **Source File & Lines**: `scripts/run_real_study_b_v2.py`, lines 88-101
- **Evidence**: Zero-landslide cells assigned constant 2.5 degrees; non-zero cells assigned RASTERVALU mean of failure sites.

## Step 1: Independent Terrain Extraction
- **Data Source**: CGIAR SRTM 90m Version 4.1 GeoTIFF mosaic (tiles 51_10, 52_10, 51_11, 52_11)
- **Computed Variables**: `slope_dem_mean`, `slope_dem_p90`, `frac_pixels_over_25deg`, `elev_mean`

## Step 2.A: Centrality Re-Analysis (Independent Slope Control)
### Kerala-Only Cells (N = 48)
| Metric | Plain ρ | Raw p | Holm p | 95% Bootstrap CI | Partial ρ (Slope-Ctrl) | Perm p (10k) | Holm Perm p | Spatial CI (0.75° blocks) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Degree** | -0.1447 | 0.3265 | 0.6530 | [-0.446, +0.173] | +0.4062 | 0.0035 | 0.0140 | [-0.090, +0.638] |
| **Betweenness** | -0.1847 | 0.2089 | 0.6266 | [-0.466, +0.099] | +0.2042 | 0.1708 | 0.1994 | [-0.249, +0.520] |
| **Clustering** | -0.0986 | 0.5048 | 0.6530 | [-0.422, +0.203] | +0.2440 | 0.0997 | 0.1994 | [-0.055, +0.539] |
| **Eigenvector** | -0.2319 | 0.1127 | 0.4507 | [-0.514, +0.067] | +0.3234 | 0.0248 | 0.0744 | [-0.111, +0.580] |
### All Active Cells (N = 97)
| Metric | Plain ρ | Raw p | Holm p | 95% Bootstrap CI | Partial ρ (Slope-Ctrl) | Perm p (10k) | Holm Perm p | Spatial CI (0.75° blocks) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Degree** | +0.0595 | 0.5627 | 1.0000 | [-0.144, +0.253] | +0.4357 | 0.0001 | 0.0004 | [+0.208, +0.569] |
| **Betweenness** | +0.0588 | 0.5673 | 1.0000 | [-0.162, +0.264] | +0.3203 | 0.0015 | 0.0015 | [+0.118, +0.464] |
| **Clustering** | -0.0283 | 0.7831 | 1.0000 | [-0.225, +0.181] | +0.3612 | 0.0004 | 0.0008 | [+0.156, +0.558] |
| **Eigenvector** | +0.0005 | 0.9958 | 1.0000 | [-0.187, +0.200] | +0.3883 | 0.0001 | 0.0004 | [+0.146, +0.527] |

## Step 2.B: Leave-One-Spatial-Block-Out Cross Validation
| Dataset | Block Scale | Num Blocks | Zero / Non-zero | Null $R^2$ | Slope $R^2$ | Slope + Net $R^2$ | Null AUC | Slope AUC | Slope + Net AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Kerala (48) | 0.50deg | 18 | 14/34 | -0.0493 | +0.1129 | +0.0767 | 0.500 | 0.842 | 0.838 |
| Kerala (48) | 0.75deg | 13 | 14/34 | -0.0886 | +0.0513 | +0.1302 | 0.500 | 0.821 | 0.815 |
| Kerala (48) | 1.00deg | 8 | 14/34 | -0.0720 | +0.0803 | +0.0273 | 0.500 | 0.838 | 0.838 |
| All (97) | 0.50deg | 33 | 53/44 | -0.0266 | +0.0833 | +0.0789 | 0.500 | 0.852 | 0.872 |
| All (97) | 0.75deg | 18 | 53/44 | -0.0492 | +0.0324 | +0.0664 | 0.500 | 0.858 | 0.877 |
| All (97) | 1.00deg | 12 | 53/44 | -0.0477 | +0.0544 | +0.0100 | 0.500 | 0.851 | 0.873 |

## Step 2.C: Positive Control (Event Rainfall)
### Kerala (48)
* **August 2018 Total Rain**: plain $\rho = +0.3310$ ($p = 0.021549$), slope-controlled partial $\rho = +0.2938$ ($p = 0.0429$)
* **Jun-Aug 2018 Extreme Days**: plain $\rho = +0.3310$ ($p = 0.021578$), slope-controlled partial $\rho = +0.3026$ ($p = 0.034$)
### All (97)
* **August 2018 Total Rain**: plain $\rho = +0.3712$ ($p = 0.00018208$), slope-controlled partial $\rho = +0.3651$ ($p = 0.0002$)
* **Jun-Aug 2018 Extreme Days**: plain $\rho = +0.3333$ ($p = 0.0008491$), slope-controlled partial $\rho = +0.2827$ ($p = 0.0047$)

## Step 2.D: Point-Level Validation (4,728 Landslides vs 4,728 Background Points)
* **Slope Only**: Mean AUC = 0.836 (spread: [0.616, 1.000], SD = 0.096)
* **Slope + Event Rainfall**: Mean AUC = 0.830 (spread: [0.623, 0.994], SD = 0.095)
* **Slope + Rainfall + Hub Distance**: Mean AUC = 0.832 (spread: [0.625, 0.994], SD = 0.091)

## Step 2.E: Exploratory Jun-Aug 2018 Event-Window Network
### Kerala (48)
* **2018 Degree**: plain $\rho = +0.2682$ ($p = 0.0653$), slope-controlled partial $\rho = +0.2236$ ($p = 0.1244$)
* **2018 Betweenness**: plain $\rho = +0.0317$ ($p = 0.8309$), slope-controlled partial $\rho = +0.0016$ ($p = 0.991$)
* **2018 Clustering**: plain $\rho = -0.0189$ ($p = 0.8986$), slope-controlled partial $\rho = +0.3522$ ($p = 0.0143$)
* **2018 Eigenvector**: plain $\rho = +0.4200$ ($p = 0.003$), slope-controlled partial $\rho = +0.3998$ ($p = 0.0046$)
### All (97)
* **2018 Degree**: plain $\rho = +0.2757$ ($p = 0.0063$), slope-controlled partial $\rho = +0.2533$ ($p = 0.0112$)
* **2018 Betweenness**: plain $\rho = +0.1928$ ($p = 0.0585$), slope-controlled partial $\rho = +0.1363$ ($p = 0.1808$)
* **2018 Clustering**: plain $\rho = +0.0318$ ($p = 0.7574$), slope-controlled partial $\rho = +0.1905$ ($p = 0.0605$)
* **2018 Eigenvector**: plain $\rho = +0.4044$ ($p = 0.0$), slope-controlled partial $\rho = +0.3012$ ($p = 0.0027$)