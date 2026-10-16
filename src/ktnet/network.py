"""
network.py - Climate network construction and topological metrics.
Thresholds the ES matrix (top 5%), builds undirected weighted graph,
and computes node-level centralities (degree, betweenness, clustering, eigenvector).
"""

from pathlib import Path
from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd
import networkx as nx

def build_climate_network(
    es_matrix: np.ndarray,
    cell_ids: List[str],
    link_fraction: float = 0.05
) -> Tuple[nx.Graph, List[Dict[str, Any]], float]:
    """
    Constructs an undirected weighted network keeping the top link_fraction of Q_ij values.
    Returns (nx.Graph, links_list, threshold_value).
    """
    n = len(cell_ids)
    G = nx.Graph()

    # Add all cells as nodes
    for cid in cell_ids:
        G.add_node(cid)

    # Extract upper triangle pairs (no self-links)
    upper_indices = np.triu_indices(n, k=1)
    q_vals = es_matrix[upper_indices]

    if len(q_vals) == 0:
        return G, [], 0.0

    # Determine cutoff for top link_fraction
    k = max(1, int(np.floor(len(q_vals) * link_fraction)))
    sorted_q = np.sort(q_vals)
    cutoff = float(sorted_q[-k])

    links_list = []
    for idx in range(len(upper_indices[0])):
        i = upper_indices[0][idx]
        j = upper_indices[1][idx]
        weight = float(es_matrix[i, j])

        if weight >= cutoff and i != j:
            source = cell_ids[i]
            target = cell_ids[j]
            G.add_edge(source, target, weight=round(weight, 4))
            links_list.append({
                "source": source,
                "target": target,
                "weight": round(weight, 4)
            })

    return G, links_list, cutoff

def compute_network_metrics(
    G: nx.Graph,
    cell_ids: List[str],
    max_iter: int = 1000,
    tol: float = 1e-6
) -> pd.DataFrame:
    """
    Computes degree, betweenness, clustering, and eigenvector centralities.
    Includes robust fallback for eigenvector centrality convergence.
    """
    n = len(cell_ids)

    # Degree centrality (normalized)
    deg_dict = nx.degree_centrality(G)

    # Betweenness centrality
    bet_dict = nx.betweenness_centrality(G, normalized=True)

    # Clustering coefficient
    clust_dict = nx.clustering(G, weight="weight")

    # Eigenvector centrality with numpy solver fallback
    try:
        eig_dict = nx.eigenvector_centrality(G, max_iter=max_iter, tol=tol, weight="weight")
    except (nx.PowerIterationFailedConvergence, Exception):
        try:
            eig_dict = nx.eigenvector_centrality_numpy(G, weight="weight")
        except Exception:
            # Fallback if graph is entirely disconnected or singular
            eig_dict = {cid: deg_dict.get(cid, 0.0) for cid in cell_ids}

    metrics_records = []
    for cid in cell_ids:
        metrics_records.append({
            "cell_id": cid,
            "degree": round(float(deg_dict.get(cid, 0.0)), 4),
            "betweenness": round(float(bet_dict.get(cid, 0.0)), 4),
            "clustering": round(float(clust_dict.get(cid, 0.0)), 4),
            "eigenvector": round(float(eig_dict.get(cid, 0.0)), 4)
        })

    return pd.DataFrame(metrics_records)

def save_network_outputs(
    G: nx.Graph,
    metrics_df: pd.DataFrame,
    graphml_path: str = "data/processed/network.graphml",
    parquet_path: str = "data/processed/metrics.parquet"
) -> None:
    """Saves GraphML and parquet metrics."""
    Path(graphml_path).parent.mkdir(parents=True, exist_ok=True)
    Path(parquet_path).parent.mkdir(parents=True, exist_ok=True)

    nx.write_graphml(G, graphml_path)
    metrics_df.to_parquet(parquet_path, index=False)
