"""
tests/test_robustness.py - Unit tests for network degradation and node removal experiments.
Verifies that removal curves start at 1.0 and decrease or remain monotonic.
"""

import numpy as np
import pytest
import networkx as nx
from src.ktnet.robustness import run_node_removal_experiment

def test_removal_curves_monotonicity():
    # Connected ring lattice graph
    G = nx.cycle_graph(25)
    fractions = np.linspace(0.0, 0.50, 11)

    res = run_node_removal_experiment(
        G,
        fractions,
        strategies=["random", "degree", "betweenness"],
        n_random_runs=20,
        seed=42
    )

    # All curves must start at 1.0 (intact state)
    assert res["strategies"]["random"]["lcc_mean"][0] == 1.0
    assert res["strategies"]["random"]["eff_mean"][0] == 1.0
    assert res["strategies"]["degree"]["lcc"][0] == 1.0
    assert res["strategies"]["degree"]["eff"][0] == 1.0
    assert res["strategies"]["betweenness"]["lcc"][0] == 1.0
    assert res["strategies"]["betweenness"]["eff"][0] == 1.0

    # At 50% removal, values must decrease
    assert res["strategies"]["degree"]["lcc"][-1] < 1.0
    assert res["strategies"]["degree"]["eff"][-1] < 1.0
    assert res["strategies"]["random"]["lcc_mean"][-1] < 1.0
