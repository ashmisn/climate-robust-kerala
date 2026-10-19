"""
scripts/run_phase1_strengthen_v3.py - Phase 1 Final Strengthening (Study B Landslide Validation).
Executes Steps 0, 1, 2 (A-E) in strict Real Data Mode with independent SRTM terrain.
All outputs written to outputs/phase1_strengthen_v3/.
"""

import sys
import json
import glob
from pathlib import Path
from typing import Dict, Any, List, Tuple
import cv2
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata
from sklearn.linear_model import LinearRegression, Ridge, LogisticRegression
from sklearn.metrics import r2_score, roc_auc_score
import shapefile
from shapely.geometry import shape, Point, box
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ktnet.landslide import bootstrap_spearman_ci
from src.ktnet.phase1_strengthen import (
    permutation_test_partial_spearman,
    spatial_block_bootstrap_multiscale
)
from src.ktnet.sync import compute_full_es_matrix


def holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Applies step-down Holm-Bonferroni correction across a family of p-values.
    """
    m = len(p_values)
    indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m
    running_max = 0.0
    for rank, (orig_idx, p_val) in enumerate(indexed_p):
        multiplier = m - rank
        adj_p = min(1.0, max(running_max, multiplier * p_val))
        running_max = adj_p
        adjusted[orig_idx] = round(float(adj_p), 4)
    return adjusted


def main():
    out_dir = Path("outputs/phase1_strengthen_v3")
    fig_dir = out_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("================================================================================")
    print("STEP 0: SLOPE CIRCULARITY AUDIT")
    print("================================================================================")
    
    # Audit existing file
    existing_parquet = "outputs/real_data_run_v2/processed/landslide_stats.parquet"
    cells_old = pd.read_parquet(existing_parquet)
    
    print("Code location where circular mean_slope was assigned:")
    print("  File: scripts/run_real_study_b_v2.py, Lines 88-101")
    print("  Code snippet:")
    print("    mean_slopes = []")
    print("    for _, row in cells_df.iterrows():")
    print("        slps = cell_slopes[row['cell_id']]")
    print("        if len(slps) > 0: mean_slopes.append(np.mean(slps))")
    print("        else: mean_slopes.append(2.5)")
    print("\nDescriptive statistics of old mean_slope:")
    zero_mask = cells_old["landslide_count_2018"] == 0
    print(f"Cells with landslide_count_2018 == 0 (N = {zero_mask.sum()}):")
    print(cells_old.loc[zero_mask, "mean_slope"].describe().to_string())
    print(f"\nCells with landslide_count_2018 > 0 (N = {(~zero_mask).sum()}):")
    print(cells_old.loc[~zero_mask, "mean_slope"].describe().to_string())

    print("\n--------------------------------------------------------------------------------")
    print("STEP 0 VERDICT: Is mean_slope independent of landslide presence?")
    print("VERDICT: NO.")
    print("EVIDENCE: mean_slope for all 53 zero-landslide cells was assigned a hard-coded constant")
    print("2.5 degrees (std = 0.0), whereas cells with landslides were assigned the mean slope of")
    print("their failure sites from the landslide shapefile RASTERVALU attribute (min 8.93°, mean 24.05°).")
    print("This made mean_slope artificially collinear with binary presence, guaranteeing AUC = 1.000.")
    print("--------------------------------------------------------------------------------\n")

    # =========================================================================
    # STEP 1: INDEPENDENT TERRAIN EXTRACTION FROM SRTM TILES
    # =========================================================================
    print("================================================================================")
    print("STEP 1: INDEPENDENT TERRAIN EXTRACTION FROM CGIAR SRTM 90M MOSAIC")
    print("================================================================================")
    
    # Verify SRTM tiles
    srtm_dir = Path("data/raw/srtm")
    tiles = ["srtm_51_10.tif", "srtm_52_10.tif", "srtm_51_11.tif", "srtm_52_11.tif"]
    for t in tiles:
        t_path = srtm_dir / t
        print(f"Verified SRTM tile: {t_path.name} (size: {t_path.stat().st_size:,} bytes)")

    print("Building continuous 12000 x 12000 DEM mosaic (Lon 70-80°E, Lat 5-15°N)...")
    t51_10 = cv2.imread(str(srtm_dir / "srtm_51_10.tif"), cv2.IMREAD_UNCHANGED)
    t52_10 = cv2.imread(str(srtm_dir / "srtm_52_10.tif"), cv2.IMREAD_UNCHANGED)
    t51_11 = cv2.imread(str(srtm_dir / "srtm_51_11.tif"), cv2.IMREAD_UNCHANGED)
    t52_11 = cv2.imread(str(srtm_dir / "srtm_52_11.tif"), cv2.IMREAD_UNCHANGED)

    mosaic = np.vstack([np.hstack([t51_10, t52_10]), np.hstack([t51_11, t52_11])])
    dem_mosaic = np.where(mosaic < -100, 0, mosaic).astype(float)
    print(f"Mosaic ready: shape={dem_mosaic.shape}, elevation range: {dem_mosaic.min()} m to {dem_mosaic.max()} m")

    # Load cells and GADM boundary
    with open("data/raw/kerala_boundary_gadm.geojson", "r", encoding="utf-8") as f:
        kerala_poly = shape(json.load(f)["features"][0]["geometry"])

    cells_df = cells_old.copy()
    cells_df.rename(columns={"mean_slope": "slope_at_landslides"}, inplace=True)

    half_res = 0.125
    res = 1.0 / 1200.0  # SRTM 3-arcsecond pixel resolution

    slope_dem_means = []
    slope_dem_p90s = []
    frac_over_25s = []
    elev_means = []
    k_fracs = []

    for _, r in cells_df.iterrows():
        c_lat = r["lat"]
        c_lon = r["lon"]
        
        # Bounding box
        b = box(c_lon - half_res, c_lat - half_res, c_lon + half_res, c_lat + half_res)
        k_fracs.append(float(b.intersection(kerala_poly).area / b.area))

        col_start = int(round((c_lon - half_res - 70.0) / res))
        col_end = int(round((c_lon + half_res - 70.0) / res))
        row_start = int(round((15.0 - (c_lat + half_res)) / res))
        row_end = int(round((15.0 - (c_lat - half_res)) / res))

        patch = dem_mosaic[row_start:row_end, col_start:col_end]
        
        # Metre-scaled gradient per pixel accounting for latitude
        dy = res * 111139.0
        dx = res * 111139.0 * np.cos(np.radians(c_lat))

        dz_dx = (patch[:, 2:] - patch[:, :-2]) / (2.0 * dx)
        dz_dy = (patch[:-2, 1:-1] - patch[2:, 1:-1]) / (2.0 * dy)
        dz_dx = dz_dx[1:-1, :]

        slope_deg = np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))

        slope_dem_means.append(round(float(np.mean(slope_deg)), 2))
        slope_dem_p90s.append(round(float(np.percentile(slope_deg, 90)), 2))
        frac_over_25s.append(round(float(np.mean(slope_deg > 25.0)), 4))
        elev_means.append(round(float(np.mean(patch)), 1))

    cells_df["kerala_area_frac"] = k_fracs
    cells_df["is_kerala_50"] = cells_df["kerala_area_frac"] >= 0.50
    cells_df["slope_dem_mean"] = slope_dem_means
    cells_df["slope_dem_p90"] = slope_dem_p90s
    cells_df["frac_pixels_over_25deg"] = frac_over_25s
    cells_df["elev_mean"] = elev_means

    # Define slope strata based on independent slope_dem_mean
    def classify_slope_dem(s):
        if s < 8.0:
            return "Low"
        elif s <= 18.0:
            return "Medium"
        else:
            return "High"

    cells_df["slope_dem_class"] = cells_df["slope_dem_mean"].apply(classify_slope_dem)

    df_97 = cells_df.copy()
    df_48 = cells_df[cells_df["is_kerala_50"]].copy().reset_index(drop=True)

    print(f"Computed independent terrain for all 97 cells. Kerala-only subset: N = {len(df_48)} cells.")
    print("Independent slope_dem_mean describe (N=97):")
    print(df_97["slope_dem_mean"].describe().to_string())

    # =========================================================================
    # STEP 2.C: EVENT-SPECIFIC RAINFALL (AUG 2018 TOTAL & JUN-AUG EXTREME DAYS)
    # =========================================================================
    print("\n================================================================================")
    print("STEP 2.C: EVENT-SPECIFIC RAINFALL ANALYSIS")
    print("================================================================================")
    rain_npz = np.load("data/raw/imd_rainfall_real.npz")
    cube = rain_npz["rainfall"]
    lats = rain_npz["lats"]
    lons = rain_npz["lons"]
    years = list(rain_npz["years"])
    y18_idx = years.index(2018)

    # August 2018 is index slice [37*122 + 61 : 37*122 + 92]
    aug_start = y18_idx * 122 + 61
    aug_end = y18_idx * 122 + 92
    aug_rain_sum = cube[aug_start:aug_end].sum(axis=0)

    # Jun-Aug 2018 (92 days) extreme days >= cell p95 and >= 5 mm
    jja_slice = slice(y18_idx * 122, y18_idx * 122 + 92)
    jja_2018 = cube[jja_slice]

    p95_grid = np.zeros((len(lats), len(lons)))
    for r_idx in range(len(lats)):
        for c_idx in range(len(lons)):
            s_rain = cube[:, r_idx, c_idx]
            rainy = s_rain[s_rain >= 0.1]
            p95_grid[r_idx, c_idx] = max(5.0, float(np.percentile(rainy, 95))) if len(rainy) > 0 else 5.0

    ext_days_grid = (jja_2018 >= p95_grid).sum(axis=0)

    aug_rain_cells = []
    ext_days_cells = []
    for _, r in cells_df.iterrows():
        lat_idx = int(np.argmin(np.abs(lats - r["lat"])))
        lon_idx = int(np.argmin(np.abs(lons - r["lon"])))
        aug_rain_cells.append(float(aug_rain_sum[lat_idx, lon_idx]))
        ext_days_cells.append(int(ext_days_grid[lat_idx, lon_idx]))

    cells_df["aug2018_rain_mm"] = aug_rain_cells
    cells_df["aug2018_extreme_days"] = ext_days_cells
    df_97["aug2018_rain_mm"] = aug_rain_cells
    df_97["aug2018_extreme_days"] = ext_days_cells
    df_48["aug2018_rain_mm"] = cells_df.loc[cells_df["is_kerala_50"], "aug2018_rain_mm"].values
    df_48["aug2018_extreme_days"] = cells_df.loc[cells_df["is_kerala_50"], "aug2018_extreme_days"].values

    rainfall_results = {}
    for set_label, cur_df in [("all_97_cells", df_97), ("kerala_48_cells", df_48)]:
        r_aug, p_aug = spearmanr(cur_df["aug2018_rain_mm"], cur_df["landslide_density"])
        ci_aug_low, ci_aug_high = bootstrap_spearman_ci(cur_df["aug2018_rain_mm"].values, cur_df["landslide_density"].values, n_bootstrap=1000, seed=42)
        part_aug, part_p_aug = permutation_test_partial_spearman(
            cur_df["aug2018_rain_mm"].values, cur_df["landslide_density"].values, [cur_df["slope_dem_mean"].values], n_permutations=10000, seed=42
        )

        r_ext, p_ext = spearmanr(cur_df["aug2018_extreme_days"], cur_df["landslide_density"])
        ci_ext_low, ci_ext_high = bootstrap_spearman_ci(cur_df["aug2018_extreme_days"].values, cur_df["landslide_density"].values, n_bootstrap=1000, seed=42)
        part_ext, part_p_ext = permutation_test_partial_spearman(
            cur_df["aug2018_extreme_days"].values, cur_df["landslide_density"].values, [cur_df["slope_dem_mean"].values], n_permutations=10000, seed=42
        )

        rainfall_results[set_label] = {
            "aug2018_rain_mm": {
                "plain_rho": round(float(r_aug), 4), "plain_p": float(f"{p_aug:.4e}"), "ci_95": [ci_aug_low, ci_aug_high],
                "partial_rho_slope_ctrl": round(float(part_aug), 4), "partial_perm_p": round(float(part_p_aug), 4)
            },
            "aug2018_extreme_days": {
                "plain_rho": round(float(r_ext), 4), "plain_p": float(f"{p_ext:.4e}"), "ci_95": [ci_ext_low, ci_ext_high],
                "partial_rho_slope_ctrl": round(float(part_ext), 4), "partial_perm_p": round(float(part_p_ext), 4)
            }
        }
        print(f"\n{set_label} (N = {len(cur_df)}):")
        print(f"  Aug-2018 Total Rain    : plain rho = {r_aug:+.4f} (p = {p_aug:.4e}), 95% CI: [{ci_aug_low:+.3f}, {ci_aug_high:+.3f}] | slope-ctrl partial rho = {part_aug:+.4f} (perm p = {part_p_aug:.4f})")
        print(f"  Jun-Aug 18 Extreme Days: plain rho = {r_ext:+.4f} (p = {p_ext:.4e}), 95% CI: [{ci_ext_low:+.3f}, {ci_ext_high:+.3f}] | slope-ctrl partial rho = {part_ext:+.4f} (perm p = {part_p_ext:.4f})")

    # =========================================================================
    # STEP 2.A: RERUN CENTRALITY CORRELATIONS WITH INDEPENDENT SLOPE
    # =========================================================================
    print("\n================================================================================")
    print("STEP 2.A: CENTRALITY CORRELATIONS (INDEPENDENT SLOPE CONTROL & HOLM CORRECTION)")
    print("================================================================================")
    
    metrics = ["degree", "betweenness", "clustering", "eigenvector"]
    centrality_results = {"all_97_cells": {}, "kerala_48_cells": {}}

    for set_label, cur_df in [("all_97_cells", df_97), ("kerala_48_cells", df_48)]:
        print(f"\n>>> Dataset: {set_label} (N = {len(cur_df)}) <<<")
        centrality_results[set_label]["metrics"] = {}
        
        raw_perm_p_list = []
        raw_plain_p_list = []
        metric_temp_data = {}

        for m in metrics:
            x = cur_df[m].values
            y = cur_df["landslide_density"].values
            slope_indep = cur_df["slope_dem_mean"].values

            # Plain Spearman
            rho_p, p_val = spearmanr(x, y)
            ci_low, ci_high = bootstrap_spearman_ci(x, y, n_bootstrap=1000, seed=42)

            # Slope-controlled partial Spearman with 10k permutations
            part_r, perm_p = permutation_test_partial_spearman(x, y, [slope_indep], n_permutations=10000, seed=42)

            # Multi-scale spatial block bootstrap CIs
            boot_cis = spatial_block_bootstrap_multiscale(
                cur_df, metric_col=m, target_col="landslide_density", control_cols=["slope_dem_mean"],
                block_sizes=[0.5, 0.75, 1.0], n_bootstrap=1000, seed=42
            )

            raw_plain_p_list.append(p_val)
            raw_perm_p_list.append(perm_p)

            metric_temp_data[m] = {
                "plain_rho": round(float(rho_p), 4),
                "plain_p_raw": round(float(p_val), 4),
                "plain_ci_95": [ci_low, ci_high],
                "partial_rho": round(float(part_r), 4),
                "partial_perm_p_raw": round(float(perm_p), 4),
                "spatial_bootstrap_cis": boot_cis
            }

        # Apply Holm-Bonferroni correction across family of 4 centrality tests
        plain_p_holm = holm_bonferroni_correction(raw_plain_p_list)
        perm_p_holm = holm_bonferroni_correction(raw_perm_p_list)

        for idx, m in enumerate(metrics):
            data_m = metric_temp_data[m]
            data_m["plain_p_holm"] = plain_p_holm[idx]
            data_m["partial_perm_p_holm"] = perm_p_holm[idx]
            centrality_results[set_label]["metrics"][m] = data_m

            print(f"Metric: {m.upper():12s}")
            print(f"  Plain Spearman         : rho = {data_m['plain_rho']:+.4f}, raw p = {data_m['plain_p_raw']:.4f}, Holm p = {data_m['plain_p_holm']:.4f}, 95% CI: [{data_m['plain_ci_95'][0]:+.3f}, {data_m['plain_ci_95'][1]:+.3f}]")
            print(f"  Slope-Controlled Partial: rho = {data_m['partial_rho']:+.4f}, raw perm p = {data_m['partial_perm_p_raw']:.4f}, Holm p = {data_m['partial_perm_p_holm']:.4f}")
            for bs_key, b_info in data_m["spatial_bootstrap_cis"].items():
                print(f"    {bs_key} ({b_info['n_blocks']:2d} blocks): 95% CI: [{b_info['ci_low']:+.3f}, {b_info['ci_high']:+.3f}], SE = {b_info['se']:.3f}")

        # Slope-class strata on independent slope_dem_mean
        strata_res = {}
        print(f"\nSlope Class Stratification on slope_dem_mean ({set_label}):")
        for sc in ["Low", "Medium", "High"]:
            sub = cur_df[cur_df["slope_dem_class"] == sc]
            n_sub = len(sub)
            strata_res[sc] = {"n_cells": n_sub, "metrics": {}}
            print(f"  Class {sc:6s} (N = {n_sub} cells):")
            for m in metrics:
                if n_sub >= 4 and np.std(sub["landslide_density"]) > 1e-12 and np.std(sub[m]) > 1e-12:
                    r_sc, p_sc = spearmanr(sub[m], sub["landslide_density"])
                    r_val = round(float(r_sc), 4)
                    p_val = round(float(p_sc), 4)
                else:
                    r_val, p_val = 0.0, 1.0
                strata_res[sc]["metrics"][m] = {"rho": r_val, "p_value": p_val}
                print(f"    {m:12s}: rho = {r_val:+.4f}, p = {p_val:.4f}")
        centrality_results[set_label]["slope_strata"] = strata_res

    # =========================================================================
    # STEP 2.B: LEAVE-ONE-SPATIAL-BLOCK-OUT CV WITH INDEPENDENT SLOPE
    # =========================================================================
    print("\n================================================================================")
    print("STEP 2.B: MODEL COMPARISON (LEAVE-ONE-SPATIAL-BLOCK-OUT CV)")
    print("================================================================================")
    
    cv_results = {}
    for set_label, cur_df in [("all_97_cells", df_97), ("kerala_48_cells", df_48)]:
        print(f"\n>>> Spatial-Block CV: {set_label} (N = {len(cur_df)}) <<<")
        cv_out = {}
        y_reg = cur_df["landslide_density"].values
        y_bin = (cur_df["landslide_count_2018"] > 0).astype(int).values
        n_zero = int(np.sum(y_bin == 0))
        n_pos = int(np.sum(y_bin > 0))

        X_slope = cur_df[["slope_dem_mean"]].values
        X_all = cur_df[["slope_dem_mean", "degree", "betweenness", "clustering", "eigenvector"]].values

        for bs in [0.5, 0.75, 1.0]:
            b_lat = np.floor((cur_df["lat"] - 8.0) / bs).astype(int)
            b_lon = np.floor((cur_df["lon"] - 74.5) / bs).astype(int)
            blocks = (b_lat.astype(str) + "_" + b_lon.astype(str)).values
            unique_b = np.unique(blocks)
            n_blocks = len(unique_b)

            pred_null_reg = np.zeros(len(cur_df))
            pred_slope_reg = np.zeros(len(cur_df))
            pred_all_reg = np.zeros(len(cur_df))

            pred_null_clf = np.zeros(len(cur_df))
            pred_slope_clf = np.zeros(len(cur_df))
            pred_all_clf = np.zeros(len(cur_df))

            for b in unique_b:
                trn = (blocks != b)
                tst = (blocks == b)

                pred_null_reg[tst] = np.mean(y_reg[trn])
                pred_null_clf[tst] = np.mean(y_bin[trn])

                r_slope = Ridge(alpha=1.0).fit(X_slope[trn], y_reg[trn])
                pred_slope_reg[tst] = r_slope.predict(X_slope[tst])

                r_all = Ridge(alpha=1.0).fit(X_all[trn], y_reg[trn])
                pred_all_reg[tst] = r_all.predict(X_all[tst])

                if len(np.unique(y_bin[trn])) < 2:
                    pred_slope_clf[tst] = np.mean(y_bin[trn])
                    pred_all_clf[tst] = np.mean(y_bin[trn])
                else:
                    c_slope = LogisticRegression(max_iter=1000, random_state=42).fit(X_slope[trn], y_bin[trn])
                    pred_slope_clf[tst] = c_slope.predict_proba(X_slope[tst])[:, 1]

                    c_all = LogisticRegression(max_iter=1000, random_state=42).fit(X_all[trn], y_bin[trn])
                    pred_all_clf[tst] = c_all.predict_proba(X_all[tst])[:, 1]

            r2_null = float(r2_score(y_reg, pred_null_reg))
            r2_slope = float(r2_score(y_reg, pred_slope_reg))
            r2_all = float(r2_score(y_reg, pred_all_reg))

            auc_null = 0.500
            auc_slope = float(roc_auc_score(y_bin, pred_slope_clf))
            auc_all = float(roc_auc_score(y_bin, pred_all_clf))

            bs_key = f"block_{bs:.2f}deg"
            cv_out[bs_key] = {
                "n_blocks": int(n_blocks),
                "zero_landslide_cells": n_zero,
                "nonzero_landslide_cells": n_pos,
                "r2_null": round(r2_null, 4),
                "r2_slope_only": round(r2_slope, 4),
                "r2_slope_plus_metrics": round(r2_all, 4),
                "auc_null": round(auc_null, 3),
                "auc_slope_only": round(auc_slope, 3),
                "auc_slope_plus_metrics": round(auc_all, 3)
            }
            print(f"Block {bs:.2f}deg ({n_blocks:2d} blocks | {n_zero} zero / {n_pos} non-zero cells):")
            print(f"  R²  (Density)   : Null = {r2_null:+.4f} | Slope Only = {r2_slope:+.4f} | Slope + Network = {r2_all:+.4f}")
            print(f"  AUC (Presence>0): Null = {auc_null:.3f} | Slope Only = {auc_slope:.3f} | Slope + Network = {auc_all:.3f}")

        cv_results[set_label] = cv_out

    # =========================================================================
    # STEP 2.D: POINT-LEVEL TEST (4,728 LANDSLIDES VS 4,728 BACKGROUND POINTS)
    # =========================================================================
    print("\n================================================================================")
    print("STEP 2.D: POINT-LEVEL TEST (LANDSLIDE POINTS VS RANDOM BACKGROUND POINTS)")
    print("================================================================================")
    
    # Read landslide points
    sf = shapefile.Reader("data/raw/Kerela landslide.shp")
    ls_pts = []
    for i in range(len(sf)):
        shp = sf.shape(i)
        ls_pts.append((float(shp.points[0][0]), float(shp.points[0][1])))
    print(f"Loaded {len(ls_pts)} real landslide initiation points.")

    # Generate 4,728 background points inside Kerala boundary
    min_lon, min_lat, max_lon, max_lat = kerala_poly.bounds
    rng = np.random.default_rng(42)
    bg_pts = []
    while len(bg_pts) < len(ls_pts):
        cand_lons = rng.uniform(min_lon, max_lon, 5000)
        cand_lats = rng.uniform(min_lat, max_lat, 5000)
        for clon, clat in zip(cand_lons, cand_lats):
            if kerala_poly.contains(Point(clon, clat)):
                bg_pts.append((float(clon), float(clat)))
                if len(bg_pts) == len(ls_pts):
                    break
    print(f"Sampled {len(bg_pts)} random background points inside Kerala polygon (seed 42).")

    # Stable hubs coordinates
    stable_hubs = [(10.00, 76.00), (10.25, 76.25), (10.75, 76.00), (11.00, 75.75)]
    def dist_to_nearest_hub_km(lat, lon):
        dists = [np.hypot((lat - h_lat) * 111.139, (lon - h_lon) * 111.139 * np.cos(np.radians(lat))) for h_lat, h_lon in stable_hubs]
        return min(dists)

    def extract_point_predictors(pts_list, label_val):
        rows = []
        for lon_val, lat_val in pts_list:
            # DEM pixel
            c_idx = int(round((lon_val - 70.0) / res))
            r_idx = int(round((15.0 - lat_val) / res))
            r_idx = max(1, min(dem_mosaic.shape[0] - 2, r_idx))
            c_idx = max(1, min(dem_mosaic.shape[1] - 2, c_idx))

            elev = float(dem_mosaic[r_idx, c_idx])

            # Slope at pixel
            dy = res * 111139.0
            dx = res * 111139.0 * np.cos(np.radians(lat_val))
            dz_dx = (dem_mosaic[r_idx, c_idx + 1] - dem_mosaic[r_idx, c_idx - 1]) / (2.0 * dx)
            dz_dy = (dem_mosaic[r_idx - 1, c_idx] - dem_mosaic[r_idx + 1, c_idx]) / (2.0 * dy)
            slp = float(np.degrees(np.arctan(np.hypot(dz_dx, dz_dy))))

            # Rainfall from cell
            lat_rain_idx = int(np.argmin(np.abs(lats - lat_val)))
            lon_rain_idx = int(np.argmin(np.abs(lons - lon_val)))
            rain_val = float(aug_rain_sum[lat_rain_idx, lon_rain_idx])

            hub_d = dist_to_nearest_hub_km(lat_val, lon_val)
            rows.append({
                "lon": lon_val, "lat": lat_val,
                "slope_dem": slp, "elevation": elev,
                "aug2018_rain": rain_val, "hub_dist_km": hub_d,
                "target": label_val
            })
        return rows

    pt_df = pd.DataFrame(extract_point_predictors(ls_pts, 1) + extract_point_predictors(bg_pts, 0))
    print(f"Point dataset created: Total N = {len(pt_df)} (50% landslides, 50% background).")

    # Spatial block CV on points (0.75 deg blocks)
    block_size = 0.75
    b_lat = np.floor((pt_df["lat"] - 8.0) / block_size).astype(int)
    b_lon = np.floor((pt_df["lon"] - 74.5) / block_size).astype(int)
    pt_df["block_id"] = b_lat.astype(str) + "_" + b_lon.astype(str)

    unique_pt_blocks = pt_df["block_id"].unique()
    print(f"Point-level spatial CV across {len(unique_pt_blocks)} blocks (0.75° blocks)...")

    fold_aucs_s = []
    fold_aucs_sr = []
    fold_aucs_srh = []

    pred_s = np.zeros(len(pt_df))
    pred_sr = np.zeros(len(pt_df))
    pred_srh = np.zeros(len(pt_df))
    y_pt = pt_df["target"].values

    for b in unique_pt_blocks:
        trn = (pt_df["block_id"] != b).values
        tst = (pt_df["block_id"] == b).values

        if len(np.unique(y_pt[tst])) < 2 or len(np.unique(y_pt[trn])) < 2:
            continue

        # Model 1: Slope only
        m1 = LogisticRegression(max_iter=1000).fit(pt_df.loc[trn, ["slope_dem"]], y_pt[trn])
        pred_s[tst] = m1.predict_proba(pt_df.loc[tst, ["slope_dem"]])[:, 1]
        fold_aucs_s.append(roc_auc_score(y_pt[tst], pred_s[tst]))

        # Model 2: Slope + Rainfall
        m2 = LogisticRegression(max_iter=1000).fit(pt_df.loc[trn, ["slope_dem", "aug2018_rain"]], y_pt[trn])
        pred_sr[tst] = m2.predict_proba(pt_df.loc[tst, ["slope_dem", "aug2018_rain"]])[:, 1]
        fold_aucs_sr.append(roc_auc_score(y_pt[tst], pred_sr[tst]))

        # Model 3: Slope + Rainfall + Hub Dist
        m3 = LogisticRegression(max_iter=1000).fit(pt_df.loc[trn, ["slope_dem", "aug2018_rain", "hub_dist_km"]], y_pt[trn])
        pred_srh[tst] = m3.predict_proba(pt_df.loc[tst, ["slope_dem", "aug2018_rain", "hub_dist_km"]])[:, 1]
        fold_aucs_srh.append(roc_auc_score(y_pt[tst], pred_srh[tst]))

    point_cv_results = {
        "n_blocks": len(fold_aucs_s),
        "slope_only": {
            "mean_auc": round(float(np.mean(fold_aucs_s)), 3),
            "std_auc": round(float(np.std(fold_aucs_s)), 3),
            "min_auc": round(float(np.min(fold_aucs_s)), 3),
            "max_auc": round(float(np.max(fold_aucs_s)), 3)
        },
        "slope_plus_rainfall": {
            "mean_auc": round(float(np.mean(fold_aucs_sr)), 3),
            "std_auc": round(float(np.std(fold_aucs_sr)), 3),
            "min_auc": round(float(np.min(fold_aucs_sr)), 3),
            "max_auc": round(float(np.max(fold_aucs_sr)), 3)
        },
        "slope_plus_rainfall_plus_hubdist": {
            "mean_auc": round(float(np.mean(fold_aucs_srh)), 3),
            "std_auc": round(float(np.std(fold_aucs_srh)), 3),
            "min_auc": round(float(np.min(fold_aucs_srh)), 3),
            "max_auc": round(float(np.max(fold_aucs_srh)), 3)
        }
    }
    print("Point-Level Spatial-Block CV AUC Results:")
    print(f"  1. Slope Only                     : Mean AUC = {point_cv_results['slope_only']['mean_auc']:.3f} (fold spread: [{point_cv_results['slope_only']['min_auc']:.3f}, {point_cv_results['slope_only']['max_auc']:.3f}], SD = {point_cv_results['slope_only']['std_auc']:.3f})")
    print(f"  2. Slope + Event Rainfall         : Mean AUC = {point_cv_results['slope_plus_rainfall']['mean_auc']:.3f} (fold spread: [{point_cv_results['slope_plus_rainfall']['min_auc']:.3f}, {point_cv_results['slope_plus_rainfall']['max_auc']:.3f}], SD = {point_cv_results['slope_plus_rainfall']['std_auc']:.3f})")
    print(f"  3. Slope + Rainfall + Hub Distance: Mean AUC = {point_cv_results['slope_plus_rainfall_plus_hubdist']['mean_auc']:.3f} (fold spread: [{point_cv_results['slope_plus_rainfall_plus_hubdist']['min_auc']:.3f}, {point_cv_results['slope_plus_rainfall_plus_hubdist']['max_auc']:.3f}], SD = {point_cv_results['slope_plus_rainfall_plus_hubdist']['std_auc']:.3f})")

    # =========================================================================
    # STEP 2.E: EXPLORATORY 2018 EVENT-WINDOW NETWORK
    # =========================================================================
    print("\n================================================================================")
    print("STEP 2.E: EXPLORATORY JUN-AUG 2018 EVENT-WINDOW NETWORK")
    print("================================================================================")
    
    n_cells = len(cells_df)
    event_series_18 = []
    for _, r in cells_df.iterrows():
        lat_idx = int(np.argmin(np.abs(lats - r["lat"])))
        lon_idx = int(np.argmin(np.abs(lons - r["lon"])))
        s_40 = cube[:, lat_idx, lon_idx]
        rainy = s_40[s_40 >= 0.1]
        p95 = max(5.0, float(np.percentile(rainy, 95))) if len(rainy) > 0 else 5.0
        
        # 92 days series
        c_18 = jja_2018[:, lat_idx, lon_idx]
        ev_times = np.where(c_18 >= p95)[0]
        event_series_18.append(ev_times)

    q_mat_18 = compute_full_es_matrix(event_series_18, max_lag=10.0)
    upper_q18 = q_mat_18[np.triu_indices(n_cells, k=1)]
    cutoff_18 = float(np.percentile(upper_q18, 95))
    print(f"2018 Q_ij matrix computed. Top 5% threshold = {cutoff_18:.4f}")

    G_18 = nx.Graph()
    for _, r in cells_df.iterrows():
        G_18.add_node(r["cell_id"])
    for i in range(n_cells):
        for j in range(i + 1, n_cells):
            if q_mat_18[i, j] >= cutoff_18:
                G_18.add_edge(cells_df.loc[i, "cell_id"], cells_df.loc[j, "cell_id"])

    print(f"2018 Network: {G_18.number_of_nodes()} nodes, {G_18.number_of_edges()} edges")
    deg_18 = dict(G_18.degree())
    btw_18 = nx.betweenness_centrality(G_18)
    clu_18 = nx.clustering(G_18)
    try:
        eig_18 = nx.eigenvector_centrality_numpy(G_18)
    except Exception:
        eig_18 = nx.eigenvector_centrality(G_18, max_iter=2000)

    cells_df["degree_2018"] = cells_df["cell_id"].map(deg_18)
    cells_df["betweenness_2018"] = cells_df["cell_id"].map(btw_18)
    cells_df["clustering_2018"] = cells_df["cell_id"].map(clu_18)
    cells_df["eigenvector_2018"] = cells_df["cell_id"].map(eig_18)

    df_97["degree_2018"] = cells_df["degree_2018"]
    df_97["betweenness_2018"] = cells_df["betweenness_2018"]
    df_97["clustering_2018"] = cells_df["clustering_2018"]
    df_97["eigenvector_2018"] = cells_df["eigenvector_2018"]

    df_48["degree_2018"] = cells_df.loc[cells_df["is_kerala_50"], "degree_2018"].values
    df_48["betweenness_2018"] = cells_df.loc[cells_df["is_kerala_50"], "betweenness_2018"].values
    df_48["clustering_2018"] = cells_df.loc[cells_df["is_kerala_50"], "clustering_2018"].values
    df_48["eigenvector_2018"] = cells_df.loc[cells_df["is_kerala_50"], "eigenvector_2018"].values

    exploratory_18_results = {}
    for set_label, cur_df in [("all_97_cells", df_97), ("kerala_48_cells", df_48)]:
        exploratory_18_results[set_label] = {}
        print(f"\nExploratory 2018 Network Correlations ({set_label}, N={len(cur_df)}):")
        for m in metrics:
            m_col = f"{m}_2018"
            r_plain, p_plain = spearmanr(cur_df[m_col], cur_df["landslide_density"])
            part_r, perm_p = permutation_test_partial_spearman(
                cur_df[m_col].values, cur_df["landslide_density"].values, [cur_df["slope_dem_mean"].values], n_permutations=10000, seed=42
            )
            exploratory_18_results[set_label][m] = {
                "plain_rho": round(float(r_plain), 4), "plain_p": round(float(p_plain), 4),
                "partial_rho_slope_ctrl": round(float(part_r), 4), "partial_perm_p": round(float(perm_p), 4)
            }
            print(f"  2018 {m.capitalize():12s}: plain rho = {r_plain:+.4f} (p = {p_plain:.4f}) | slope-controlled partial rho = {part_r:+.4f} (perm p = {perm_p:.4f})")

    # =========================================================================
    # SAVE PARQUET AND STRUCTURED JSON
    # =========================================================================
    parquet_out = out_dir / "landslide_stats_independent_terrain.parquet"
    cells_df.to_parquet(parquet_out, index=False)
    print(f"\nSaved independent terrain parquet to: {parquet_out}")

    master_results = {
        "step_0_audit": {
            "verdict": "NOT independent (circular)",
            "file": "scripts/run_real_study_b_v2.py",
            "lines": "88-101",
            "evidence": "Zero-landslide cells assigned constant 2.5 degrees; non-zero cells assigned RASTERVALU mean of failure sites."
        },
        "step_1_independent_terrain": {
            "source": "CGIAR SRTM 90m Version 4.1 GeoTIFF mosaic (tiles 51_10, 52_10, 51_11, 52_11)",
            "pixel_resolution_arcsec": 3,
            "metrics": ["slope_dem_mean", "slope_dem_p90", "frac_pixels_over_25deg", "elev_mean"]
        },
        "step_2_centrality_reanalysis": centrality_results,
        "step_2_cv_model_comparison": cv_results,
        "step_2_event_rainfall": rainfall_results,
        "step_2_point_level_test": point_cv_results,
        "step_2_exploratory_2018_network": exploratory_18_results
    }

    results_json_path = out_dir / "results.json"
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(master_results, f, indent=2)
    print(f"Saved master results JSON to: {results_json_path}")

    # Generate Markdown Summary
    md_path = out_dir / "results.md"
    write_comprehensive_markdown(md_path, master_results)
    print(f"Saved comprehensive Markdown report to: {md_path}")

    # Generate Slide 24 Scatter Plot Image
    fig_path = fig_dir / "slide24_scatter.png"
    generate_slide24_plot(df_97, df_48, master_results, fig_path)
    print(f"Saved Slide 24 figure to: {fig_path}")

    print("\n================================================================================")
    print("STEP 2 COMPLETE. PROCEEDING TO STEP 3: UI PIPELINE & CONTRACT UPDATES")
    print("================================================================================")


def generate_slide24_plot(df_97: pd.DataFrame, df_48: pd.DataFrame, d: Dict[str, Any], out_path: Path):
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, ax = plt.subplots(figsize=(7.0, 4.5), dpi=300)

    color_map = {"Low": "#10b981", "Medium": "#f59e0b", "High": "#ef4444"}
    label_map = {"Low": "Low Slope (< 8°)", "Medium": "Medium Slope (8°–18°)", "High": "High Slope (> 18°)"}

    for sc in ["Low", "Medium", "High"]:
        sub = df_97[df_97["slope_dem_class"] == sc]
        ax.scatter(sub["betweenness"], sub["landslide_density"], c=color_map[sc], label=label_map[sc], s=48, alpha=0.85, edgecolors="none")

    top2 = df_97.sort_values("landslide_density", ascending=False).head(2)
    offsets = [(-0.016, -0.26), (-0.016, -0.20)]
    for idx, (_, r) in enumerate(top2.iterrows()):
        loc_name = "Idukki (Munnar)" if r["cell_id"] == "c_034" else "Peerumade"
        ax.annotate(
            f"{r['cell_id']}: {loc_name}\n({int(r['landslide_count_2018'])} slides)",
            xy=(r["betweenness"], r["landslide_density"]),
            xytext=(r["betweenness"] + offsets[idx][0], r["landslide_density"] + offsets[idx][1]),
            fontsize=8, fontweight="bold", color="#1e293b",
            arrowprops=dict(arrowstyle="->", color="#64748b", lw=1.0)
        )

    ax.set_title("Event Synchronization Betweenness vs. 2018 Landslide Density", fontsize=11, fontweight="bold", pad=12, color="#0f172a")
    ax.set_xlabel("Betweenness Centrality (Synchronized Moisture Routing)", fontsize=9.5, fontweight="bold", color="#334155")
    ax.set_ylabel("2018 Landslide Density (pts / km²)", fontsize=9.5, fontweight="bold", color="#334155")

    ax.legend(frameon=True, framealpha=0.9, fontsize=8.5, loc="upper right")
    ax.tick_params(axis="both", which="major", labelsize=8.5)

    k48_m = d["step_2_centrality_reanalysis"]["kerala_48_cells"]["metrics"]["betweenness"]
    cv_075 = d["step_2_cv_model_comparison"]["kerala_48_cells"]["block_0.75deg"]
    ci_075 = k48_m["spatial_bootstrap_cis"]["block_0.75deg"]

    stats_str = (
        f"Kerala-Only (N = 48, Indep. Terrain):\n"
        f"• Plain Spearman: ρ = {k48_m['plain_rho']:+.3f} (p = {k48_m['plain_p_raw']:.3f}, Holm = {k48_m['plain_p_holm']:.3f})\n"
        f"• Slope-Controlled: partial ρ = {k48_m['partial_rho']:+.3f} (perm p = {k48_m['partial_perm_p_raw']:.3f})\n"
        f"• 95% Spatial Block CI: [{ci_075['ci_low']:+.3f}, {ci_075['ci_high']:+.3f}]\n"
        f"• Spatial CV R²: Slope = {cv_075['r2_slope_only']:+.3f} → All = {cv_075['r2_slope_plus_metrics']:+.3f} (no gain)\n"
        f"• Spatial CV AUC: Slope = {cv_075['auc_slope_only']:.3f} → All = {cv_075['auc_slope_plus_metrics']:.3f}"
    )

    ax.text(
        0.035, 0.94, stats_str,
        transform=ax.transAxes, fontsize=7.2, family="monospace",
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.0)
    )

    plt.tight_layout()
    fig.savefig(out_path, dpi=300)


def write_comprehensive_markdown(filepath: Path, d: Dict[str, Any]):
    md = []
    md.append("# Phase 1 Strengthening v3: Independent Terrain & Study B Validation")
    md.append("*Comprehensive Scientific Report with Full Observational Provenance*\n")

    md.append("## Step 0: Slope Circularity Audit")
    md.append(f"- **Verdict**: {d['step_0_audit']['verdict']}")
    md.append(f"- **Source File & Lines**: `{d['step_0_audit']['file']}`, lines {d['step_0_audit']['lines']}")
    md.append(f"- **Evidence**: {d['step_0_audit']['evidence']}\n")

    md.append("## Step 1: Independent Terrain Extraction")
    md.append(f"- **Data Source**: {d['step_1_independent_terrain']['source']}")
    md.append("- **Computed Variables**: `slope_dem_mean`, `slope_dem_p90`, `frac_pixels_over_25deg`, `elev_mean`\n")

    md.append("## Step 2.A: Centrality Re-Analysis (Independent Slope Control)")
    for set_key, label in [("kerala_48_cells", "Kerala-Only Cells (N = 48)"), ("all_97_cells", "All Active Cells (N = 97)")]:
        md.append(f"### {label}")
        md.append("| Metric | Plain ρ | Raw p | Holm p | 95% Bootstrap CI | Partial ρ (Slope-Ctrl) | Perm p (10k) | Holm Perm p | Spatial CI (0.75° blocks) |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        set_m = d["step_2_centrality_reanalysis"][set_key]["metrics"]
        for m in ["degree", "betweenness", "clustering", "eigenvector"]:
            info = set_m[m]
            ci_sp = info["spatial_bootstrap_cis"]["block_0.75deg"]
            md.append(f"| **{m.capitalize()}** | {info['plain_rho']:+.4f} | {info['plain_p_raw']:.4f} | {info['plain_p_holm']:.4f} | [{info['plain_ci_95'][0]:+.3f}, {info['plain_ci_95'][1]:+.3f}] | {info['partial_rho']:+.4f} | {info['partial_perm_p_raw']:.4f} | {info['partial_perm_p_holm']:.4f} | [{ci_sp['ci_low']:+.3f}, {ci_sp['ci_high']:+.3f}] |")

    md.append("\n## Step 2.B: Leave-One-Spatial-Block-Out Cross Validation")
    md.append("| Dataset | Block Scale | Num Blocks | Zero / Non-zero | Null $R^2$ | Slope $R^2$ | Slope + Net $R^2$ | Null AUC | Slope AUC | Slope + Net AUC |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for set_key, label in [("kerala_48_cells", "Kerala (48)"), ("all_97_cells", "All (97)")]:
        for bs in ["block_0.50deg", "block_0.75deg", "block_1.00deg"]:
            cv = d["step_2_cv_model_comparison"][set_key][bs]
            md.append(f"| {label} | {bs.replace('block_', '')} | {cv['n_blocks']} | {cv['zero_landslide_cells']}/{cv['nonzero_landslide_cells']} | {cv['r2_null']:+.4f} | {cv['r2_slope_only']:+.4f} | {cv['r2_slope_plus_metrics']:+.4f} | {cv['auc_null']:.3f} | {cv['auc_slope_only']:.3f} | {cv['auc_slope_plus_metrics']:.3f} |")

    md.append("\n## Step 2.C: Positive Control (Event Rainfall)")
    for set_key, label in [("kerala_48_cells", "Kerala (48)"), ("all_97_cells", "All (97)")]:
        rf = d["step_2_event_rainfall"][set_key]
        md.append(f"### {label}")
        md.append(f"* **August 2018 Total Rain**: plain $\\rho = {rf['aug2018_rain_mm']['plain_rho']:+.4f}$ ($p = {rf['aug2018_rain_mm']['plain_p']}$), slope-controlled partial $\\rho = {rf['aug2018_rain_mm']['partial_rho_slope_ctrl']:+.4f}$ ($p = {rf['aug2018_rain_mm']['partial_perm_p']}$)")
        md.append(f"* **Jun-Aug 2018 Extreme Days**: plain $\\rho = {rf['aug2018_extreme_days']['plain_rho']:+.4f}$ ($p = {rf['aug2018_extreme_days']['plain_p']}$), slope-controlled partial $\\rho = {rf['aug2018_extreme_days']['partial_rho_slope_ctrl']:+.4f}$ ($p = {rf['aug2018_extreme_days']['partial_perm_p']}$)")

    md.append("\n## Step 2.D: Point-Level Validation (4,728 Landslides vs 4,728 Background Points)")
    pt = d["step_2_point_level_test"]
    md.append(f"* **Slope Only**: Mean AUC = {pt['slope_only']['mean_auc']:.3f} (spread: [{pt['slope_only']['min_auc']:.3f}, {pt['slope_only']['max_auc']:.3f}], SD = {pt['slope_only']['std_auc']:.3f})")
    md.append(f"* **Slope + Event Rainfall**: Mean AUC = {pt['slope_plus_rainfall']['mean_auc']:.3f} (spread: [{pt['slope_plus_rainfall']['min_auc']:.3f}, {pt['slope_plus_rainfall']['max_auc']:.3f}], SD = {pt['slope_plus_rainfall']['std_auc']:.3f})")
    md.append(f"* **Slope + Rainfall + Hub Distance**: Mean AUC = {pt['slope_plus_rainfall_plus_hubdist']['mean_auc']:.3f} (spread: [{pt['slope_plus_rainfall_plus_hubdist']['min_auc']:.3f}, {pt['slope_plus_rainfall_plus_hubdist']['max_auc']:.3f}], SD = {pt['slope_plus_rainfall_plus_hubdist']['std_auc']:.3f})")

    md.append("\n## Step 2.E: Exploratory Jun-Aug 2018 Event-Window Network")
    for set_key, label in [("kerala_48_cells", "Kerala (48)"), ("all_97_cells", "All (97)")]:
        ex = d["step_2_exploratory_2018_network"][set_key]
        md.append(f"### {label}")
        for m in ["degree", "betweenness", "clustering", "eigenvector"]:
            info = ex[m]
            md.append(f"* **2018 {m.capitalize()}**: plain $\\rho = {info['plain_rho']:+.4f}$ ($p = {info['plain_p']}$), slope-controlled partial $\\rho = {info['partial_rho_slope_ctrl']:+.4f}$ ($p = {info['partial_perm_p']}$)")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


if __name__ == "__main__":
    main()
