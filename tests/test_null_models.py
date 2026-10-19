"""
tests/test_null_models.py - Unit tests for size-matched basin removal null models.
Tests scattered and contiguous null generation on a deterministic toy lattice graph.
"""

import pytest
import numpy as np
import pandas as pd
import networkx as nx

from src.ktnet.null_models import (
    compute_subset_removal_impact,
    get_k_nearest_cells,
    run_basin_size_matched_null_experiment
)


def test_compute_subset_removal_impact_toy():
    # Simple line graph: 0 - 1 - 2 - 3 - 4 (5 nodes)
    G = nx.path_graph(5)
    # Removing middle node (2) splits into [0, 1] and [3, 4] -> LCC drops from 5 to 2
    lcc_drop, eff_drop = compute_subset_removal_impact(
        G, nodes_to_remove={2}, intact_lcc=5, intact_eff=1.0, initial_n=5, compute_efficiency=True
    )
    # intact LCC = 5, remaining LCC = 2 -> drop = (5 - 2)/5 = 0.60
    assert lcc_drop == 0.60
    assert eff_drop > 0.0


def test_get_k_nearest_cells_deterministic():
    coords = {
        "c_1": (10.0, 76.0),
        "c_2": (10.25, 76.0),
        "c_3": (10.5, 76.0),
        "c_4": (11.0, 76.0),
    }
    candidate_nodes = ["c_1", "c_2", "c_3", "c_4"]
    nearest_2 = get_k_nearest_cells("c_1", 2, coords, candidate_nodes)
    assert nearest_2 == ["c_1", "c_2"]

    nearest_3 = get_k_nearest_cells("c_3", 3, coords, candidate_nodes)
    # c_3 dist to c_3 is 0, dist to c_2 is 0.25, dist to c_4 is 0.50, dist to c_1 is 0.50
    assert nearest_3[0] == "c_3"
    assert nearest_3[1] == "c_2"
    assert len(nearest_3) == 3


def test_run_basin_size_matched_null_experiment_toy():
    # 3x3 grid graph (9 nodes)
    G = nx.grid_2d_graph(3, 3)
    # Relabel nodes to strings
    mapping = {node: f"c_{node[0]}_{node[1]}" for node in G.nodes()}
    G = nx.relabel_nodes(G, mapping)

    cell_records = []
    for node in G.nodes():
        parts = node.split("_")
        i, j = int(parts[1]), int(parts[2])
        basin_id = "basin_A" if i < 2 else "basin_B"
        basin_name = "Basin A" if i < 2 else "Basin B"
        cell_records.append({
            "cell_id": node,
            "lat": 10.0 + i * 0.25,
            "lon": 76.0 + j * 0.25,
            "basin_id": basin_id,
            "basin_name": basin_name
        })
    df_cells = pd.DataFrame(cell_records)

    summary_df, raw_dict = run_basin_size_matched_null_experiment(
        G, df_cells, n_draws=50, seed=42
    )

    assert len(summary_df) == 2
    assert "basin_id" in summary_df.columns
    assert "observed_lcc_drop" in summary_df.columns
    assert "scattered_lcc_pvalue" in summary_df.columns
    assert "contiguous_lcc_pvalue" in summary_df.columns

    # Verify percentiles ordering
    for _, row in summary_df.iterrows():
        assert row["scattered_lcc_p05"] <= row["scattered_lcc_p95"]
        assert row["contiguous_lcc_p05"] <= row["contiguous_lcc_p95"]
        assert 0.0 <= row["scattered_lcc_pvalue"] <= 1.0
        assert 0.0 <= row["contiguous_lcc_pvalue"] <= 1.0
