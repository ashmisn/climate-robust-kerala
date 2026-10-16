"""
robustness.py - Study A: Network robustness and basin vulnerability.
Implements targeted & random node removal experiments (LCC and global efficiency),
basin group removal impact ranking, and sensitivity across event percentiles (90/95/97).
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import spearmanr

def compute_lcc_size(G: nx.Graph) -> int:
    """Returns size of the largest connected component."""
    if len(G) == 0:
        return 0
    return len(max(nx.connected_components(G), key=len))

def compute_global_efficiency(G: nx.Graph, initial_n: int = None) -> float:
    """
    Computes average inverse shortest path distance between all pairs of nodes.
    Normalized by initial network size N*(N-1) per Latora & Marchiori (2001).
    """
    n = len(G)
    if n <= 1:
        return 0.0
    N = initial_n if (initial_n is not None and initial_n > 1) else n
    lengths = dict(nx.all_pairs_shortest_path_length(G))
    inv_sum = 0.0
    for u, dists in lengths.items():
        for v, d in dists.items():
            if u != v and d > 0:
                inv_sum += 1.0 / d
    return float(inv_sum / (N * (N - 1)))

def run_node_removal_experiment(
    G: nx.Graph,
    removal_fractions: np.ndarray,
    strategies: List[str] = ["random", "degree", "betweenness"],
    n_random_runs: int = 100,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Simulates node attack and random failure from fraction 0.0 to 0.50.
    Tracks LCC and Global Efficiency, normalized to the intact network (starting at 1.0).
    """
    np.random.seed(seed)
    nodes = list(G.nodes())
    n_nodes = len(nodes)

    intact_lcc = max(1, compute_lcc_size(G))
    intact_eff = max(1e-9, compute_global_efficiency(G, initial_n=n_nodes))

    # Pre-rank nodes for targeted strategies
    deg_dict = nx.degree_centrality(G)
    bet_dict = nx.betweenness_centrality(G)

    sorted_by_deg = sorted(nodes, key=lambda n: deg_dict.get(n, 0.0), reverse=True)
    sorted_by_bet = sorted(nodes, key=lambda n: bet_dict.get(n, 0.0), reverse=True)

    results = {
        "fractions": [round(float(f), 4) for f in removal_fractions],
        "metrics": ["lcc", "efficiency"],
        "strategies": {
            "random": {
                "lcc_mean": [],
                "lcc_std": [],
                "eff_mean": [],
                "eff_std": []
            },
            "degree": {
                "lcc": [],
                "eff": []
            },
            "betweenness": {
                "lcc": [],
                "eff": []
            }
        }
    }

    # Targeted: Degree and Betweenness
    for strat, sorted_nodes in [("degree", sorted_by_deg), ("betweenness", sorted_by_bet)]:
        for f in removal_fractions:
            num_remove = int(np.round(f * n_nodes))
            to_remove = set(sorted_nodes[:num_remove])
            subG = G.subgraph([n for n in nodes if n not in to_remove])

            norm_lcc = compute_lcc_size(subG) / intact_lcc
            norm_eff = compute_global_efficiency(subG, initial_n=n_nodes) / intact_eff

            results["strategies"][strat]["lcc"].append(round(float(norm_lcc), 4))
            results["strategies"][strat]["eff"].append(round(float(norm_eff), 4))

    # Random strategy (100 Monte Carlo runs)
    for f in removal_fractions:
        num_remove = int(np.round(f * n_nodes))
        lcc_runs = []
        eff_runs = []

        for _ in range(n_random_runs):
            if num_remove == 0:
                to_remove = set()
            else:
                to_remove = set(np.random.choice(nodes, size=num_remove, replace=False))

            subG = G.subgraph([n for n in nodes if n not in to_remove])
            lcc_runs.append(compute_lcc_size(subG) / intact_lcc)
            eff_runs.append(compute_global_efficiency(subG, initial_n=n_nodes) / intact_eff)

        results["strategies"]["random"]["lcc_mean"].append(round(float(np.mean(lcc_runs)), 4))
        results["strategies"]["random"]["lcc_std"].append(round(float(np.std(lcc_runs)), 4))
        results["strategies"]["random"]["eff_mean"].append(round(float(np.mean(eff_runs)), 4))
        results["strategies"]["random"]["eff_std"].append(round(float(np.std(eff_runs)), 4))

    return results

def compute_basin_impact(
    G: nx.Graph,
    cells_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Evaluates topological impact of removing whole river basin node groups.
    Computes drop in LCC and Global Efficiency when each basin is removed.
    """
    n_nodes = len(G)
    intact_lcc = max(1, compute_lcc_size(G))
    intact_eff = max(1e-9, compute_global_efficiency(G, initial_n=n_nodes))

    basin_groups = cells_df.groupby("basin_id")
    records = []

    for basin_id, group in basin_groups:
        basin_name = group["basin_name"].iloc[0]
        basin_nodes = set(group["cell_id"].tolist())
        n_cells = len(basin_nodes)

        remaining_nodes = [n for n in G.nodes() if n not in basin_nodes]
        subG = G.subgraph(remaining_nodes)

        rem_lcc = compute_lcc_size(subG) / intact_lcc
        rem_eff = compute_global_efficiency(subG, initial_n=n_nodes) / intact_eff

        lcc_drop = round(float(max(0.0, 1.0 - rem_lcc)), 4)
        eff_drop = round(float(max(0.0, 1.0 - rem_eff)), 4)

        records.append({
            "basin_id": basin_id,
            "name": basin_name,
            "n_cells": n_cells,
            "lcc_drop_if_removed": lcc_drop,
            "efficiency_drop_if_removed": eff_drop,
            "composite_impact": round(0.6 * lcc_drop + 0.4 * eff_drop, 4)
        })

    df = pd.DataFrame(records)
    df = df.sort_values(by="composite_impact", ascending=False).reset_index(drop=True)
    df["impact_rank"] = range(1, len(df) + 1)
    return df

def find_critical_nodes(
    G: nx.Graph,
    cells_df: pd.DataFrame,
    top_k: int = 15
) -> List[Dict[str, Any]]:
    """
    Finds top-k critical cells whose individual removal causes the greatest LCC drop.
    """
    intact_lcc = max(1, compute_lcc_size(G))
    node_to_basin = dict(zip(cells_df["cell_id"], cells_df["basin_id"]))

    impacts = []
    for node in G.nodes():
        remaining = [n for n in G.nodes() if n != node]
        subG = G.subgraph(remaining)
        drop = max(0.0, 1.0 - (compute_lcc_size(subG) / intact_lcc))
        impacts.append((node, drop))

    # Sort descending by drop, secondary by degree
    deg_dict = nx.degree_centrality(G)
    impacts.sort(key=lambda item: (item[1], deg_dict.get(item[0], 0.0)), reverse=True)

    critical_nodes = []
    for rank, (cid, drop) in enumerate(impacts[:top_k], start=1):
        critical_nodes.append({
            "cell_id": cid,
            "rank": rank,
            "lcc_drop": round(float(drop), 4),
            "basin_id": node_to_basin.get(cid, "other")
        })

    return critical_nodes

def compute_sensitivity_analysis(
    networks_by_pct: Dict[int, nx.Graph],
    cells_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Computes sensitivity of critical nodes and centralities across thresholds (90, 95, 97).
    Calculates top-15 node overlap and rank correlation of degree and betweenness centralities.
    """
    top_nodes_by_pct = {}
    deg_ranks_by_pct = {}
    bet_ranks_by_pct = {}

    for p, G_p in networks_by_pct.items():
        crit = find_critical_nodes(G_p, cells_df, top_k=15)
        top_nodes_by_pct[p] = set(c["cell_id"] for c in crit)

        deg = nx.degree_centrality(G_p)
        bet = nx.betweenness_centrality(G_p)
        cell_order = cells_df["cell_id"].tolist()

        deg_ranks_by_pct[p] = [deg.get(c, 0.0) for c in cell_order]
        bet_ranks_by_pct[p] = [bet.get(c, 0.0) for c in cell_order]

    pairs = [(90, 95), (95, 97), (90, 97)]
    sensitivity_results = {}

    for p1, p2 in pairs:
        set1 = top_nodes_by_pct[p1]
        set2 = top_nodes_by_pct[p2]
        overlap_count = len(set1.intersection(set2))
        jaccard = round(overlap_count / len(set1.union(set2)), 3)

        deg_rho, _ = spearmanr(deg_ranks_by_pct[p1], deg_ranks_by_pct[p2])
        bet_rho, _ = spearmanr(bet_ranks_by_pct[p1], bet_ranks_by_pct[p2])

        key = f"{p1}_vs_{p2}"
        sensitivity_results[key] = {
            "overlap_count_top15": overlap_count,
            "jaccard_overlap": jaccard,
            "degree_rank_correlation": round(float(deg_rho), 3) if not np.isnan(deg_rho) else 1.0,
            "betweenness_rank_correlation": round(float(bet_rho), 3) if not np.isnan(bet_rho) else 1.0
        }

    return sensitivity_results
