"""
scripts/run_robustness_checks.py - Executes Study B robustness checks on independent-terrain results.
Includes:
  1. Pairwise Spearman (centrality vs slope, slope vs landslides, centrality vs landslides)
  2. Partial Spearman with 10,000 permutations and 0.75-deg spatial-block bootstrap CIs across:
     - slope_dem_mean
     - slope_dem_p90
     - frac_pixels_over_25deg
     - elev_mean
     - aug2018_rain_mm
     - all 5 controls combined
     with Holm correction (m=4) within each control set.
  3. Moran's I on regression residuals (landslide_density ~ slope_dem_mean) with 999 permutations.
  4. Tercile-stratified Spearman (Low, Medium, High slope_dem_mean).
Runs primarily on Kerala-48, and on All-97 as a sensitivity check.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata
from sklearn.linear_model import LinearRegression

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "outputs" / "phase1_strengthen_v3" / "landslide_stats_independent_terrain.parquet"
OUT_DIR = ROOT_DIR / "outputs" / "phase1_strengthen_v3" / "robustness_checks"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def holm_bonferroni(p_vals):
    m = len(p_vals)
    sorted_indices = np.argsort(p_vals)
    adj_p = np.zeros(m)
    cum_max = 0.0
    for rank, orig_idx in enumerate(sorted_indices):
        p = p_vals[orig_idx]
        adj = p * (m - rank)
        cum_max = max(cum_max, adj)
        adj_p[orig_idx] = min(1.0, cum_max)
    return adj_p.tolist()


def compute_partial_spearman(x, y, covars):
    """
    Computes partial rank correlation between x and y controlling for covars.
    covars can be a 1D array or 2D array of multiple covariates.
    """
    rx = rankdata(x).astype(float)
    ry = rankdata(y).astype(float)
    
    if isinstance(covars, list):
        rz = np.column_stack([rankdata(c).astype(float) for c in covars])
    elif len(covars.shape) == 1:
        rz = rankdata(covars).astype(float).reshape(-1, 1)
    else:
        rz = np.column_stack([rankdata(covars[:, j]).astype(float) for j in range(covars.shape[1])])
        
    lr_x = LinearRegression().fit(rz, rx)
    res_x = rx - lr_x.predict(rz)
    
    lr_y = LinearRegression().fit(rz, ry)
    res_y = ry - lr_y.predict(rz)
    
    vx = res_x - res_x.mean()
    vy = res_y - res_y.mean()
    denom = np.sqrt(np.sum(vx**2) * np.sum(vy**2))
    if denom == 0:
        return 0.0, res_x, res_y
    r = float(np.sum(vx * vy) / denom)
    return r, res_x, res_y


def permutation_test_partial(res_x, res_y, n_perm=10000, seed=42):
    rng = np.random.RandomState(seed)
    n = len(res_x)
    vx = res_x - res_x.mean()
    vy = res_y - res_y.mean()
    denom = np.sqrt(np.sum(vx**2) * np.sum(vy**2))
    if denom == 0:
        return 0.0, 1.0
    obs_r = np.sum(vx * vy) / denom
    
    vx_norm = vx / np.sqrt(np.sum(vx**2))
    vy_norm = vy / np.sqrt(np.sum(vy**2))
    
    # Generate permuted indices
    perms = np.array([rng.permutation(n) for _ in range(n_perm)])
    vy_perm = vy_norm[perms]
    null_r = np.dot(vy_perm, vx_norm)
    
    p_val = float(np.mean(np.abs(null_r) >= np.abs(obs_r) - 1e-12))
    return float(obs_r), p_val


def spatial_block_bootstrap_partial(df, x_col, y_col, covar_cols, block_size=0.75, n_boot=1000, seed=42):
    rng = np.random.RandomState(seed)
    min_lat, min_lon = df["lat"].min(), df["lon"].min()
    block_ids = (
        np.floor((df["lat"] - min_lat) / block_size).astype(int).astype(str)
        + "_"
        + np.floor((df["lon"] - min_lon) / block_size).astype(int).astype(str)
    )
    unique_blocks = np.unique(block_ids)
    n_blocks = len(unique_blocks)
    
    block_map = {b: np.where(block_ids == b)[0] for b in unique_blocks}
    
    boot_rhos = []
    for _ in range(n_boot):
        sampled_blocks = rng.choice(unique_blocks, size=n_blocks, replace=True)
        sample_indices = np.concatenate([block_map[b] for b in sampled_blocks])
        
        sub = df.iloc[sample_indices]
        if sub[y_col].nunique() <= 1:
            continue
            
        x_vals = sub[x_col].values
        y_vals = sub[y_col].values
        if isinstance(covar_cols, list):
            covar_vals = [sub[c].values for c in covar_cols]
        else:
            covar_vals = sub[covar_cols].values
            
        r_b, _, _ = compute_partial_spearman(x_vals, y_vals, covar_vals)
        boot_rhos.append(r_b)
        
    if len(boot_rhos) < 50:
        return {"ci_low": -1.0, "ci_high": 1.0, "se": 0.0, "n_blocks": n_blocks}
    return {
        "ci_low": round(float(np.percentile(boot_rhos, 2.5)), 4),
        "ci_high": round(float(np.percentile(boot_rhos, 97.5)), 4),
        "se": round(float(np.std(boot_rhos)), 4),
        "n_blocks": int(n_blocks)
    }


def compute_morans_i(coords, residuals, n_perm=999, seed=42):
    """
    Computes Moran's I on spatial residuals with Queen contiguity (distance <= 0.255 deg).
    """
    n = len(residuals)
    # Queen adjacency matrix
    W = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                dlat = abs(coords[i][0] - coords[j][0])
                dlon = abs(coords[i][1] - coords[j][1])
                if dlat <= 0.255 and dlon <= 0.255:
                    W[i, j] = 1.0
                    
    S0 = np.sum(W)
    z = residuals - np.mean(residuals)
    denom = np.sum(z**2)
    if denom == 0:
        return 0.0, 1.0, 0.0, 0.0
        
    obs_I = (n / S0) * (np.sum(W * np.outer(z, z)) / denom)
    
    # Permutation test
    rng = np.random.RandomState(seed)
    perm_I = []
    for _ in range(n_perm):
        z_perm = rng.permutation(z)
        I_p = (n / S0) * (np.sum(W * np.outer(z_perm, z_perm)) / denom)
        perm_I.append(I_p)
        
    perm_I = np.array(perm_I)
    p_val = float(np.mean(np.abs(perm_I) >= np.abs(obs_I) - 1e-12))
    expected_I = -1.0 / (n - 1)
    
    return round(float(obs_I), 4), round(p_val, 4), round(float(expected_I), 4), round(float(np.std(perm_I)), 4)


def main():
    df = pd.read_parquet(DATA_PATH)
    centrality_cols = ["degree", "betweenness", "clustering", "eigenvector"]
    
    sets = [
        ("kerala_48", df[df["is_kerala_50"]].copy().reset_index(drop=True), "Kerala-48 (Main Set, Surveyed Ground Truth)"),
        ("all_97", df.copy().reset_index(drop=True), "All-97 (Sensitivity Check, Buffer Cells Unsurveyed)")
    ]
    
    results = {}
    
    for set_key, data, set_label in sets:
        n_cells = len(data)
        print(f"\n{'='*75}")
        print(f"ANALYSIS SET: {set_label} | N = {n_cells}")
        print(f"{'='*75}")
        
        results[set_key] = {"N": n_cells, "label": set_label}
        
        # -------------------------------------------------------------
        # 1. Plain Spearman Triad
        # -------------------------------------------------------------
        print("\n--- 1. Plain Spearman Rank Correlations ---")
        triad_results = {"centrality_vs_slope": {}, "centrality_vs_landslides": {}}
        
        # slope vs landslides
        r_slope_ls, p_slope_ls = spearmanr(data["slope_dem_mean"], data["landslide_density"])
        triad_results["slope_vs_landslides"] = {"rho": round(r_slope_ls, 4), "p": round(p_slope_ls, 4)}
        print(f"slope_dem_mean vs landslide_density : rho = {r_slope_ls:+.4f} (p = {p_slope_ls:.4f})")
        
        for m in centrality_cols:
            r_cs, p_cs = spearmanr(data[m], data["slope_dem_mean"])
            r_cl, p_cl = spearmanr(data[m], data["landslide_density"])
            triad_results["centrality_vs_slope"][m] = {"rho": round(r_cs, 4), "p": round(p_cs, 4)}
            triad_results["centrality_vs_landslides"][m] = {"rho": round(r_cl, 4), "p": round(p_cl, 4)}
            print(f"  {m:<12} vs slope_dem_mean : rho = {r_cs:+.4f} (p = {p_cs:.4f})")
            print(f"  {m:<12} vs landslide_dens: rho = {r_cl:+.4f} (p = {p_cl:.4f})")
            
        results[set_key]["plain_spearman"] = triad_results
        
        # -------------------------------------------------------------
        # 2. Partial Spearman Across Different Controls
        # -------------------------------------------------------------
        print("\n--- 2. Partial Spearman Across Single & Combined Controls ---")
        controls_to_test = [
            ("slope_dem_mean", ["slope_dem_mean"], "Slope Mean"),
            ("slope_dem_p90", ["slope_dem_p90"], "Slope 90th Percentile"),
            ("frac_pixels_over_25deg", ["frac_pixels_over_25deg"], "Fraction > 25° Slope"),
            ("elev_mean", ["elev_mean"], "Elevation Mean"),
            ("aug2018_rain_mm", ["aug2018_rain_mm"], "August 2018 Rainfall (mm)"),
            ("all_combined", ["slope_dem_mean", "slope_dem_p90", "frac_pixels_over_25deg", "elev_mean", "aug2018_rain_mm"], "All 5 Controls Combined")
        ]
        
        control_results = {}
        for c_key, c_cols, c_label in controls_to_test:
            print(f"\n>> Control Set: {c_label} (cols: {c_cols})")
            ctrl_dict = {}
            p_raws = []
            rhos = []
            cis = []
            
            for m in centrality_cols:
                if len(c_cols) == 1:
                    cov_vals = data[c_cols[0]].values
                else:
                    cov_vals = data[c_cols].values
                    
                rho, rx, ry = compute_partial_spearman(data[m].values, data["landslide_density"].values, cov_vals)
                obs_r, perm_p = permutation_test_partial(rx, ry, n_perm=10000, seed=42)
                ci_dict = spatial_block_bootstrap_partial(data, m, "landslide_density", c_cols, block_size=0.75, n_boot=1000, seed=42)
                
                ctrl_dict[m] = {
                    "partial_rho": round(obs_r, 4),
                    "perm_p_raw": round(perm_p, 4),
                    "ci_075": [ci_dict["ci_low"], ci_dict["ci_high"]],
                    "se_075": ci_dict["se"]
                }
                p_raws.append(perm_p)
                rhos.append(obs_r)
                cis.append(ci_dict)
                
            p_holms = holm_bonferroni(p_raws)
            for i, m in enumerate(centrality_cols):
                ctrl_dict[m]["perm_p_holm"] = round(p_holms[i], 4)
                print(f"  {m:<12}: partial rho = {ctrl_dict[m]['partial_rho']:+.4f} | perm p = {ctrl_dict[m]['perm_p_raw']:.4f} (Holm p = {ctrl_dict[m]['perm_p_holm']:.4f}) | 95% CI: [{ctrl_dict[m]['ci_075'][0]:+.3f}, {ctrl_dict[m]['ci_075'][1]:+.3f}]")
                
            control_results[c_key] = ctrl_dict
            
        results[set_key]["partial_spearman_controls"] = control_results
        
        # -------------------------------------------------------------
        # 3. Moran's I on Residuals (landslide_density ~ slope_dem_mean)
        # -------------------------------------------------------------
        print("\n--- 3. Moran's I on Landslide Residuals (Controlled for Slope) ---")
        X = data[["slope_dem_mean"]].values
        y = data["landslide_density"].values
        lr = LinearRegression().fit(X, y)
        residuals = y - lr.predict(X)
        
        coords = data[["lat", "lon"]].values
        obs_I, p_I, exp_I, std_I = compute_morans_i(coords, residuals, n_perm=999, seed=42)
        print(f"Model: landslide_density ~ slope_dem_mean")
        print(f"Moran's I = {obs_I:+.4f} (Expected = {exp_I:.4f}, SD = {std_I:.4f}, Permutation p = {p_I:.4f})")
        results[set_key]["morans_i"] = {
            "morans_i": obs_I,
            "permutation_p": p_I,
            "expected_i": exp_I,
            "std_i": std_I
        }
        
        # -------------------------------------------------------------
        # 4. Terciles of slope_dem_mean Stratification
        # -------------------------------------------------------------
        print("\n--- 4. Tercile-Stratified Spearman on slope_dem_mean ---")
        terciles, bins = pd.qcut(data["slope_dem_mean"], q=3, retbins=True, labels=["Low", "Medium", "High"])
        data_copy = data.copy()
        data_copy["slope_tercile"] = terciles
        
        tercile_results = {"bins": [round(b, 2) for b in bins.tolist()], "strata": {}}
        print(f"Tercile Bins: {[round(b, 2) for b in bins.tolist()]}")
        
        for sc in ["Low", "Medium", "High"]:
            sub = data_copy[data_copy["slope_tercile"] == sc]
            n_sub = len(sub)
            print(f"\n  Tercile Class: {sc} (N = {n_sub} cells)")
            sc_dict = {"N": n_sub, "metrics": {}}
            for m in centrality_cols:
                r_strat, p_strat = spearmanr(sub[m], sub["landslide_density"])
                sc_dict["metrics"][m] = {"rho": round(r_strat, 4), "p": round(p_strat, 4)}
                print(f"    {m:<12}: rho = {r_strat:+.4f} (p = {p_strat:.4f})")
            tercile_results["strata"][sc] = sc_dict
            
        results[set_key]["tercile_stratification"] = tercile_results

    # Save complete JSON
    out_json = OUT_DIR / "robustness_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved comprehensive robustness results to: {out_json}")


if __name__ == "__main__":
    main()
