"""
tests/test_network.py - Unit tests for network construction and centralities.
Verifies node count, edge density matching link_fraction, and centrality bounds.
"""

import numpy as np
import pytest
import networkx as nx
from src.ktnet.network import build_climate_network, compute_network_metrics

def test_network_topology_and_centralities():
    np.random.seed(42)
    n = 20
    cell_ids = [f"c_{i:03d}" for i in range(n)]

    # Symmetric random matrix
    raw_mat = np.random.uniform(0.1, 0.9, size=(n, n)).astype(np.float32)
    es_mat = (raw_mat + raw_mat.T) / 2.0
    np.fill_diagonal(es_mat, 1.0)

    link_fraction = 0.05
    G, links, cutoff = build_climate_network(es_mat, cell_ids, link_fraction=link_fraction)

    # 1. Expected node count
    assert G.number_of_nodes() == n

    # 2. Total possible links = 20 * 19 / 2 = 190. Top 5% is floor(190 * 0.05) = 9
    expected_links = int(np.floor(190 * link_fraction))
    assert G.number_of_edges() == expected_links
    assert len(links) == expected_links

    # 3. No self-loops
    assert nx.number_of_selfloops(G) == 0

    # 4. Centrality bounds
    df_metrics = compute_network_metrics(G, cell_ids)
    assert len(df_metrics) == n
    assert (df_metrics["degree"] >= 0.0).all() and (df_metrics["degree"] <= 1.0).all()
    assert (df_metrics["betweenness"] >= 0.0).all() and (df_metrics["betweenness"] <= 1.0).all()
