# Study B Landslide Validation: Strengthened Numerical Results
*Phase 1 Final Analysis for Vyuham: Kerala Climate Network*

## 1. Cell-Level Centrality Re-Analysis (Task A)

### (a) All 97 Active Cells
| Centrality Metric | Plain Spearman ρ (p-val) | 95% Bootstrap CI | Partial ρ (Slope-Controlled) | Permutation p (10k) | Spatial CI (0.75° blocks) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Degree** | +0.0595 (0.5627) | [-0.144, +0.253] | +0.1266 | 0.2181 | [-0.186, +0.339] |
| **Betweenness** | +0.0588 (0.5673) | [-0.162, +0.264] | +0.0977 | 0.3468 | [-0.185, +0.301] |
| **Clustering** | -0.0283 (0.7831) | [-0.225, +0.181] | +0.0260 | 0.8076 | [-0.165, +0.170] |
| **Eigenvector** | +0.0005 (0.9958) | [-0.187, +0.200] | +0.1053 | 0.3043 | [-0.092, +0.226] |

### (b) Kerala-Only Cells (N = 48, >=50% inside GADM boundary)
| Centrality Metric | Plain Spearman ρ (p-val) | 95% Bootstrap CI | Partial ρ (Slope-Controlled) | Permutation p (10k) | Spatial CI (0.75° blocks) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Degree** | -0.1447 (0.3265) | [-0.446, +0.173] | +0.0153 | 0.9202 | [-0.430, +0.341] |
| **Betweenness** | -0.1847 (0.2089) | [-0.466, +0.099] | -0.0396 | 0.7903 | [-0.362, +0.276] |
| **Clustering** | -0.0986 (0.5048) | [-0.422, +0.203] | -0.0653 | 0.6656 | [-0.306, +0.258] |
| **Eigenvector** | -0.2319 (0.1127) | [-0.514, +0.067] | -0.0681 | 0.6538 | [-0.371, +0.168] |

## 2. Model Comparison: Spatial Leave-One-Block-Out CV (Task B)

Target: Landslide density (Regression $R^2$) and Binary Presence $>0$ (ROC-AUC)
| Cell Set (N) | Spatial Block Scale | Num Blocks | Null Mean $R^2$ | Slope Only $R^2$ | Slope + Metrics $R^2$ | Null AUC | Slope Only AUC | Slope + Metrics AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| All Cells (97) | 0.50deg | 33 | -0.0266 | +0.0937 | +0.0533 | 0.500 | 1.000 | 1.000 |
| All Cells (97) | 0.75deg | 18 | -0.0492 | +0.0662 | +0.0627 | 0.500 | 1.000 | 1.000 |
| All Cells (97) | 1.00deg | 12 | -0.0477 | +0.0782 | +0.0164 | 0.500 | 1.000 | 1.000 |
| Kerala Only (48) | 0.50deg | 18 | -0.0493 | +0.0503 | -0.0376 | 0.500 | 1.000 | 1.000 |
| Kerala Only (48) | 0.75deg | 13 | -0.0886 | +0.0310 | +0.0265 | 0.500 | 1.000 | 1.000 |
| Kerala Only (48) | 1.00deg | 8 | -0.0720 | +0.0367 | -0.1077 | 0.500 | 1.000 | 1.000 |

## 3. Positive Control (Task C)

* **All 97 Cells**: $\rho = +0.3712$, $p = 0.00018208$, 95% CI: [+0.169, +0.544]
* **Kerala 48 Cells**: $\rho = +0.3310$, $p = 0.021549$, 95% CI: [+0.059, +0.567]