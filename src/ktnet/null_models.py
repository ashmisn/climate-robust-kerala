"""
null_models.py - Size-matched null model experiments for river basin removals.
Evaluates whether removing a specific river basin of size k damages network connectivity
more than expected under:
  (a) Scattered null: k uniformly random cells.
  (b) Spatially contiguous null: random seed cell + k-1 nearest neighbors by grid distance.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import networkx as nx

from src.ktnet.robustness import compute_lcc_size, compute_global_efficiency


def compute_subset_removal_impact(
    G: nx.Graph,
    nodes_to_remove: set,
    intact_lcc: int,
    intact_eff: float = None,
    initial_n: int = None,
    compute_efficiency: bool = False
) -> Tuple[float, float]:
    """
    Computes LCC drop and optional Global Efficiency drop when a specific node subset is removed.
    LCC drop is defined as the fraction of the intact network's LCC:
      lcc_drop = (intact_lcc - rem_lcc) / intact_lcc
    """
    subG = G.subgraph([n for n in G.nodes() if n not in nodes_to_remove])
    rem_lcc = compute_lcc_size(subG)
    lcc_drop = float(max(0.0, 1.0 - (rem_lcc / intact_lcc)))

    eff_drop = 0.0
    if compute_efficiency and intact_eff is not None and initial_n is not None:
        rem_eff = compute_global_efficiency(subG, initial_n=initial_n)
        eff_drop = float(max(0.0, 1.0 - (rem_eff / intact_eff)))

    return round(lcc_drop, 4), round(eff_drop, 4)


def get_k_nearest_cells(
    seed_cell: str,
    k: int,
    coords: Dict[str, Tuple[float, float]],
    candidate_nodes: List[str]
) -> List[str]:
    """
    Selects k nearest cells to seed_cell by Euclidean grid distance.
    Uses (distance, cell_id) tuple for deterministic tie-breaking.
    """
    if k >= len(candidate_nodes):
        return list(candidate_nodes)

    seed_lat, seed_lon = coords[seed_cell]
    distances = []
    for node in candidate_nodes:
        lat, lon = coords[node]
        dist = np.hypot(lat - seed_lat, lon - seed_lon)
        distances.append((dist, node))

    distances.sort(key=lambda item: (item[0], item[1]))
    return [node for _, node in distances[:k]]


def precompute_spatial_neighbors(
    all_nodes: List[str],
    coords: Dict[str, Tuple[float, float]]
) -> Dict[str, List[str]]:
    """
    Precomputes distance-ordered neighbor lists for each cell to optimize contiguous null sampling.
    """
    neighbors = {}
    for seed in all_nodes:
        seed_lat, seed_lon = coords[seed]
        dists = []
        for other in all_nodes:
            olat, olon = coords[other]
            d = np.hypot(olat - seed_lat, olon - seed_lon)
            dists.append((d, other))
        dists.sort(key=lambda item: (item[0], item[1]))
        neighbors[seed] = [n for _, n in dists]
    return neighbors


def run_basin_size_matched_null_experiment(
    G: nx.Graph,
    cells_df: pd.DataFrame,
    n_draws: int = 1000,
    seed: int = 42
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]:
    """
    Executes size-matched null experiments for every basin in cells_df.

    Parameters:
      G: nx.Graph of the climate network.
      cells_df: pd.DataFrame with cell_id, lat, lon, basin_id, basin_name.
      n_draws: Number of random draws per basin size k (default: 1000).
      seed: Fixed random seed for exact reproducibility.

    Returns:
      (summary_df, raw_draws_dict):
        - summary_df: Observed drops, null means, 5th/95th percentiles, and empirical p-values.
        - raw_draws_dict: Dictionary containing raw arrays for histograms.
    """
    rng = np.random.default_rng(seed)

    all_nodes = list(G.nodes())
    n_nodes = len(all_nodes)
    intact_lcc = max(1, compute_lcc_size(G))
    intact_eff = max(1e-9, compute_global_efficiency(G, initial_n=n_nodes))

    coords = {
        row["cell_id"]: (float(row["lat"]), float(row["lon"]))
        for _, row in cells_df.iterrows()
        if row["cell_id"] in G
    }

    # Precompute distance-ordered neighbors for fast contiguous sampling
    precomputed_neighbors = precompute_spatial_neighbors(all_nodes, coords)

    basin_groups = cells_df.groupby("basin_id")
    records = []
    raw_draws_dict: Dict[str, Dict[str, Any]] = {}

    for basin_id, group in basin_groups:
        basin_name = group["basin_name"].iloc[0]
        basin_nodes = set(group["cell_id"].tolist()).intersection(G.nodes())
        k = len(basin_nodes)
        if k == 0:
            continue

        obs_lcc_drop, obs_eff_drop = compute_subset_removal_impact(
            G, basin_nodes, intact_lcc, intact_eff, initial_n=n_nodes, compute_efficiency=True
        )

        scattered_lcc = np.zeros(n_draws, dtype=np.float64)
        contiguous_lcc = np.zeros(n_draws, dtype=np.float64)

        for d in range(n_draws):
            # (a) Scattered null: uniformly random k cells
            scattered_set = set(rng.choice(all_nodes, size=k, replace=False))
            subG_scat = G.subgraph([n for n in all_nodes if n not in scattered_set])
            s_rem_lcc = compute_lcc_size(subG_scat)
            scattered_lcc[d] = float(max(0.0, 1.0 - (s_rem_lcc / intact_lcc)))

            # (b) Contiguous null: random seed cell + k-1 nearest neighbors
            seed_cell = rng.choice(all_nodes)
            contiguous_set = set(precomputed_neighbors[seed_cell][:k])
            subG_cont = G.subgraph([n for n in all_nodes if n not in contiguous_set])
            c_rem_lcc = compute_lcc_size(subG_cont)
            contiguous_lcc[d] = float(max(0.0, 1.0 - (c_rem_lcc / intact_lcc)))

        # Empirical one-sided p-value: fraction of null draws with drop >= observed
        scat_p_lcc = float(np.mean(scattered_lcc >= obs_lcc_drop))
        cont_p_lcc = float(np.mean(contiguous_lcc >= obs_lcc_drop))

        records.append({
            "basin_id": basin_id,
            "basin_name": basin_name,
            "n_cells": k,
            "observed_lcc_drop": obs_lcc_drop,
            "scattered_lcc_mean": round(float(np.mean(scattered_lcc)), 4),
            "scattered_lcc_p05": round(float(np.percentile(scattered_lcc, 5)), 4),
            "scattered_lcc_p95": round(float(np.percentile(scattered_lcc, 95)), 4),
            "scattered_lcc_pvalue": round(scat_p_lcc, 4),
            "contiguous_lcc_mean": round(float(np.mean(contiguous_lcc)), 4),
            "contiguous_lcc_p05": round(float(np.percentile(contiguous_lcc, 5)), 4),
            "contiguous_lcc_p95": round(float(np.percentile(contiguous_lcc, 95)), 4),
            "contiguous_lcc_pvalue": round(cont_p_lcc, 4),
            "observed_eff_drop": obs_eff_drop,
        })

        raw_draws_dict[basin_id] = {
            "scattered_lcc": scattered_lcc,
            "contiguous_lcc": contiguous_lcc,
            "observed_lcc_drop": obs_lcc_drop,
            "observed_eff_drop": obs_eff_drop,
            "k": k,
            "basin_name": basin_name
        }

    summary_df = pd.DataFrame(records)
    summary_df = summary_df.sort_values(by="n_cells", ascending=False).reset_index(drop=True)
    return summary_df, raw_draws_dict
