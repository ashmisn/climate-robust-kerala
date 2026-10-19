"""
src/ktnet/phase1_strengthen.py - Core functions for strengthening Study B landslide validation.
Includes permutation tests on residuals, multi-scale spatial-block bootstrap,
leave-one-spatial-block-out cross validation, and positive control event rainfall extraction.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.linear_model import LinearRegression, Ridge, LogisticRegression
from sklearn.metrics import r2_score, roc_auc_score


def permutation_test_partial_spearman(
    x: np.ndarray,
    y: np.ndarray,
    controls: List[np.ndarray],
    n_permutations: int = 10000,
    seed: int = 42
) -> Tuple[float, float]:
    """
    Computes partial Spearman correlation between x and y controlling for controls,
    and calculates a two-sided permutation p-value by shuffling the residual ranks.
    """
    rx = rankdata(x).astype(float)
    ry = rankdata(y).astype(float)

    if len(controls) == 0:
        rho, p = spearmanr(x, y)
        return float(rho), float(p)

    rz = np.column_stack([rankdata(c).astype(float) for c in controls])

    # Fit linear models on ranks to get residuals (Frisch-Waugh-Lovell)
    reg_x = LinearRegression().fit(rz, rx)
    res_x = rx - reg_x.predict(rz)

    reg_y = LinearRegression().fit(rz, ry)
    res_y = ry - reg_y.predict(rz)

    # Standardize residuals
    std_x = np.std(res_x)
    std_y = np.std(res_y)
    if std_x < 1e-12 or std_y < 1e-12:
        return 0.0, 1.0

    res_x_norm = (res_x - np.mean(res_x)) / std_x
    res_y_norm = (res_y - np.mean(res_y)) / std_y
    n = len(x)

    rho_obs = float(np.dot(res_x_norm, res_y_norm) / n)

    # Permutation test on residuals
    rng = np.random.default_rng(seed)
    perm_indices = np.array([rng.permutation(n) for _ in range(n_permutations)])
    res_y_perm = res_y_norm[perm_indices]  # Shape: (n_permutations, n)

    rho_perms = np.dot(res_y_perm, res_x_norm) / n
    extreme_count = np.sum(np.abs(rho_perms) >= np.abs(rho_obs) - 1e-12)
    # Standard unbiased Monte Carlo p-value
    p_val = float((extreme_count + 1) / (n_permutations + 1))

    return round(rho_obs, 4), round(p_val, 4)


def spatial_block_bootstrap_multiscale(
    df: pd.DataFrame,
    metric_col: str,
    target_col: str,
    control_cols: List[str],
    block_sizes: List[float] = [0.5, 0.75, 1.0],
    n_bootstrap: int = 1000,
    seed: int = 42
) -> Dict[str, Dict[str, float]]:
    """
    Computes spatial-block bootstrap 95% confidence intervals and standard errors
    for partial Spearman correlation across multiple spatial block sizes.
    """
    results = {}
    for bs in block_sizes:
        b_lat = np.floor((df["lat"] - 8.0) / bs).astype(int)
        b_lon = np.floor((df["lon"] - 74.5) / bs).astype(int)
        block_ids = (b_lat.astype(str) + "_" + b_lon.astype(str)).values
        unique_blocks = np.unique(block_ids)
        n_blocks = len(unique_blocks)

        rng = np.random.default_rng(seed)
        boot_rhos = []

        for _ in range(n_bootstrap):
            sampled_b = rng.choice(unique_blocks, size=n_blocks, replace=True)
            sampled_indices = []
            for sb in sampled_b:
                sampled_indices.extend(np.where(block_ids == sb)[0])

            b_df = df.iloc[sampled_indices]
            bx = b_df[metric_col].values
            by = b_df[target_col].values
            b_controls = [b_df[c].values for c in control_cols]

            try:
                # Direct partial correlation on sample
                rx = rankdata(bx).astype(float)
                ry = rankdata(by).astype(float)
                rz = np.column_stack([rankdata(c).astype(float) for c in b_controls])

                reg_x = LinearRegression().fit(rz, rx)
                res_x = rx - reg_x.predict(rz)
                reg_y = LinearRegression().fit(rz, ry)
                res_y = ry - reg_y.predict(rz)

                std_x, std_y = np.std(res_x), np.std(res_y)
                if std_x > 1e-12 and std_y > 1e-12:
                    r = np.corrcoef(res_x, res_y)[0, 1]
                    if not np.isnan(r):
                        boot_rhos.append(float(r))
            except Exception:
                continue

        if len(boot_rhos) > 0:
            ci_low = float(np.percentile(boot_rhos, 2.5))
            ci_high = float(np.percentile(boot_rhos, 97.5))
            se = float(np.std(boot_rhos))
        else:
            ci_low, ci_high, se = -1.0, 1.0, 0.0

        results[f"block_{bs:.2f}deg"] = {
            "n_blocks": int(n_blocks),
            "ci_low": round(ci_low, 3),
            "ci_high": round(ci_high, 3),
            "se": round(se, 3)
        }

    return results


def leave_one_block_cv(
    df: pd.DataFrame,
    block_sizes: List[float] = [0.5, 0.75, 1.0],
    seed: int = 42
) -> Dict[str, Dict[str, Any]]:
    """
    Leave-one-spatial-block-out cross validation comparing:
    - Null baseline (mean predictor)
    - Slope alone
    - Slope + 4 network metrics
    Evaluates out-of-fold R² for density and AUC for binary presence (count > 0).
    """
    results = {}
    metrics = ["degree", "betweenness", "clustering", "eigenvector"]

    y_reg = df["landslide_density"].values
    y_bin = (df["landslide_count_2018"] > 0).astype(int).values
    zero_count = int(np.sum(y_bin == 0))
    nonzero_count = int(np.sum(y_bin > 0))

    X_slope = df[["mean_slope"]].values
    X_all = df[["mean_slope"] + metrics].values

    for bs in block_sizes:
        b_lat = np.floor((df["lat"] - 8.0) / bs).astype(int)
        b_lon = np.floor((df["lon"] - 74.5) / bs).astype(int)
        blocks = (b_lat.astype(str) + "_" + b_lon.astype(str)).values
        unique_b = np.unique(blocks)
        n_blocks = len(unique_b)

        pred_null_reg = np.zeros(len(df))
        pred_slope_reg = np.zeros(len(df))
        pred_all_reg = np.zeros(len(df))

        pred_null_clf = np.zeros(len(df))
        pred_slope_clf = np.zeros(len(df))
        pred_all_clf = np.zeros(len(df))

        for b in unique_b:
            trn = (blocks != b)
            tst = (blocks == b)

            # Null mean predictors
            pred_null_reg[tst] = np.mean(y_reg[trn])
            pred_null_clf[tst] = np.mean(y_bin[trn])

            # Regression
            r_slope = Ridge(alpha=1.0).fit(X_slope[trn], y_reg[trn])
            pred_slope_reg[tst] = r_slope.predict(X_slope[tst])

            r_all = Ridge(alpha=1.0).fit(X_all[trn], y_reg[trn])
            pred_all_reg[tst] = r_all.predict(X_all[tst])

            # Classification
            if len(np.unique(y_bin[trn])) < 2:
                pred_slope_clf[tst] = np.mean(y_bin[trn])
                pred_all_clf[tst] = np.mean(y_bin[trn])
            else:
                c_slope = LogisticRegression(max_iter=1000, random_state=seed).fit(X_slope[trn], y_bin[trn])
                pred_slope_clf[tst] = c_slope.predict_proba(X_slope[tst])[:, 1]

                c_all = LogisticRegression(max_iter=1000, random_state=seed).fit(X_all[trn], y_bin[trn])
                pred_all_clf[tst] = c_all.predict_proba(X_all[tst])[:, 1]

        r2_null = float(r2_score(y_reg, pred_null_reg))
        r2_slope = float(r2_score(y_reg, pred_slope_reg))
        r2_all = float(r2_score(y_reg, pred_all_reg))

        auc_null = 0.500
        auc_slope = float(roc_auc_score(y_bin, pred_slope_clf))
        auc_all = float(roc_auc_score(y_bin, pred_all_clf))

        results[f"block_{bs:.2f}deg"] = {
            "n_blocks": int(n_blocks),
            "zero_landslide_cells": zero_count,
            "nonzero_landslide_cells": nonzero_count,
            "r2_null": round(r2_null, 4),
            "r2_slope_only": round(r2_slope, 4),
            "r2_slope_plus_metrics": round(r2_all, 4),
            "auc_null": round(auc_null, 3),
            "auc_slope_only": round(auc_slope, 3),
            "auc_slope_plus_metrics": round(auc_all, 3)
        }

    return results


def extract_august_2018_cumulative_rainfall(
    npz_path: str,
    cells_df: pd.DataFrame
) -> pd.Series:
    """
    Extracts cumulative August 2018 precipitation (mm) per grid cell from IMD rainfall cube.
    Date identification:
    - years array contains 1981-2020 (40 years)
    - JJAS season has 122 days/year (days_per_year == 122)
    - August is days 61 to 91 inclusive within the season (offset 61:92, length 31 days).
    """
    data = np.load(npz_path)
    years = list(data["years"])
    dpy = int(data["days_per_year"])
    lats = np.array(data["lats"])
    lons = np.array(data["lons"])

    y_idx = years.index(2018)
    start_2018 = y_idx * dpy
    aug_start = start_2018 + 61
    aug_end = start_2018 + 92  # 31 days of August

    aug_cube = data["rainfall"][aug_start:aug_end]
    aug_sum = aug_cube.sum(axis=0)

    cell_rainfall = []
    for _, r in cells_df.iterrows():
        lat_idx = int(np.argmin(np.abs(lats - r["lat"])))
        lon_idx = int(np.argmin(np.abs(lons - r["lon"])))
        cell_rainfall.append(float(aug_sum[lat_idx, lon_idx]))

    return pd.Series(cell_rainfall, index=cells_df.index, name="aug2018_rainfall_mm")
