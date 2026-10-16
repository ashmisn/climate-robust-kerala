"""
landslide.py - Study B: Landslide density validation and topographical stratification.
Computes landslide density per km², joins DEM slopes, calculates overall and stratified
Spearman rank correlations with bootstrap confidence intervals.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

def map_landslides_to_cells(
    landslide_points: List[Dict[str, float]],
    cells_df: pd.DataFrame,
    resolution: float = 0.25
) -> pd.DataFrame:
    """
    Counts 2018 landslide occurrences inside each cell's bounding area
    and computes density per km².
    """
    half_res = resolution / 2.0
    counts = {row["cell_id"]: 0 for _, row in cells_df.iterrows()}

    # Bounding box spatial indexing
    for pt in landslide_points:
        p_lat = pt["lat"]
        p_lon = pt["lon"]

        for _, row in cells_df.iterrows():
            cid = row["cell_id"]
            c_lat = row["lat"]
            c_lon = row["lon"]

            if (c_lat - half_res <= p_lat <= c_lat + half_res) and \
               (c_lon - half_res <= p_lon <= c_lon + half_res):
                counts[cid] += 1
                break  # Point mapped to its grid cell

    df_result = cells_df.copy()
    df_result["landslide_count_2018"] = df_result["cell_id"].map(counts)
    df_result["landslide_density"] = (df_result["landslide_count_2018"] / df_result["area_km2"]).round(5)
    return df_result

def attach_dem_slope(
    cells_df: pd.DataFrame,
    dem_slope_data: Dict[str, Dict[str, float]]
) -> pd.DataFrame:
    """
    Attaches zonal mean slope and max slope to each cell, and bins into slope tertiles.
    """
    df = cells_df.copy()
    mean_slopes = []
    max_slopes = []

    for _, row in df.iterrows():
        key = f"{row['lat']:.2f}_{row['lon']:.2f}"
        s_info = dem_slope_data.get(key, {"mean_slope": 5.0, "max_slope": 12.0})
        mean_slopes.append(s_info["mean_slope"])
        max_slopes.append(s_info["max_slope"])

    df["mean_slope"] = mean_slopes
    df["max_slope"] = max_slopes

    # Stratify into 3 tertiles: Low, Medium, High
    labels = ["Low", "Medium", "High"]
    try:
        df["slope_class"] = pd.qcut(df["mean_slope"], q=3, labels=labels, duplicates="drop")
    except Exception:
        # Fallback if ties exist
        df["slope_class"] = pd.cut(df["mean_slope"], bins=3, labels=labels)

    return df

def bootstrap_spearman_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_bootstrap: int = 1000,
    alpha: float = 0.05,
    seed: int = 42
) -> Tuple[float, float]:
    """
    Computes empirical bootstrap confidence interval for Spearman rank correlation.
    """
    np.random.seed(seed)
    n = len(x)
    if n < 4:
        return -1.0, 1.0

    rhos = []
    for _ in range(n_bootstrap):
        idx = np.random.choice(n, size=n, replace=True)
        r, _ = spearmanr(x[idx], y[idx])
        if not np.isnan(r):
            rhos.append(r)

    if len(rhos) == 0:
        return 0.0, 0.0

    low_p = (alpha / 2.0) * 100
    high_p = (1.0 - alpha / 2.0) * 100
    ci_low = float(np.percentile(rhos, low_p))
    ci_high = float(np.percentile(rhos, high_p))
    return round(ci_low, 3), round(ci_high, 3)

def compute_landslide_correlations(
    df: pd.DataFrame,
    metrics: List[str] = ["degree", "betweenness", "clustering", "eigenvector"],
    n_bootstrap: int = 1000
) -> Dict[str, Any]:
    """
    Computes overall Spearman correlation and slope-stratified correlations
    with bootstrap 95% confidence intervals.
    """
    y = df["landslide_density"].values
    overall = {}

    for m in metrics:
        x = df[m].values
        rho, p = spearmanr(x, y)
        rho_val = round(float(rho), 3) if not np.isnan(rho) else 0.0
        p_val = round(float(p), 4) if not np.isnan(p) else 1.0
        ci_low, ci_high = bootstrap_spearman_ci(x, y, n_bootstrap=n_bootstrap)

        overall[m] = {
            "rho": rho_val,
            "p": p_val,
            "ci_low": ci_low,
            "ci_high": ci_high
        }

    # Stratified by slope class
    by_slope_class = []
    for s_class, sub_df in df.groupby("slope_class"):
        n_sub = len(sub_df)
        y_sub = sub_df["landslide_density"].values

        for m in metrics:
            x_sub = sub_df[m].values
            if n_sub >= 3:
                rho, p = spearmanr(x_sub, y_sub)
                r_val = round(float(rho), 3) if not np.isnan(rho) else 0.0
                p_val = round(float(p), 4) if not np.isnan(p) else 1.0
            else:
                r_val, p_val = 0.0, 1.0

            by_slope_class.append({
                "class": str(s_class),
                "n": n_sub,
                "metric": m,
                "rho": r_val,
                "p": p_val
            })

    # Scatter records for dashboard plotting
    scatter = []
    for _, row in df.iterrows():
        scatter.append({
            "cell_id": row["cell_id"],
            "density": float(row["landslide_density"]),
            "slope": float(row["mean_slope"]),
            "slope_class": str(row.get("slope_class", "Medium")),
            "degree": float(row["degree"]),
            "betweenness": float(row["betweenness"]),
            "clustering": float(row["clustering"]),
            "eigenvector": float(row["eigenvector"]),
            "extreme_days_aug2018": int(row.get("extreme_days_aug2018", 0))
        })

    return {
        "overall": overall,
        "by_slope_class": by_slope_class,
        "scatter": scatter
    }
