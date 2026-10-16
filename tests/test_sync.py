"""
tests/test_sync.py - Unit tests for Event Synchronization (Quian Quiroga et al. 2002).
Verifies:
1. Symmetry: Q_ij == Q_ji
2. Bounds: Q in [0, 1]
3. Identical series yield high Q (Q ≈ 1.0)
4. Independent random series yield low Q (Q close to 0)
"""

import numpy as np
import pytest
from src.ktnet.sync import pair_event_synchronization, compute_full_es_matrix

def test_sync_symmetry_and_bounds():
    np.random.seed(42)
    s1 = np.sort(np.random.choice(1000, 50, replace=False)).astype(np.float64)
    s2 = np.sort(np.random.choice(1000, 45, replace=False)).astype(np.float64)

    q12 = pair_event_synchronization(s1, s2, max_lag=10.0)
    q21 = pair_event_synchronization(s2, s1, max_lag=10.0)

    assert abs(q12 - q21) < 1e-6, f"ES not symmetric: {q12} vs {q21}"
    assert 0.0 <= q12 <= 1.0, f"Q out of bounds: {q12}"

def test_identical_series_high_q():
    s = np.array([10, 25, 40, 70, 110, 150, 200, 260], dtype=np.float64)
    q = pair_event_synchronization(s, s, max_lag=10.0)
    assert q >= 0.95, f"Identical series should have Q ≈ 1, got {q}"

def test_independent_series_low_q():
    np.random.seed(123)
    # Series spaced far apart in time
    s1 = np.array([10, 50, 90, 140, 200], dtype=np.float64)
    s2 = np.array([25, 65, 115, 170, 230], dtype=np.float64)  # gaps exceed max_lag=5
    q = pair_event_synchronization(s1, s2, max_lag=5.0)
    assert q == 0.0 or q < 0.15, f"Independent far series should have very low Q, got {q}"

def test_full_es_matrix_properties():
    np.random.seed(99)
    series_list = [
        np.sort(np.random.choice(500, 30, replace=False)).astype(np.float64)
        for _ in range(5)
    ]
    mat = compute_full_es_matrix(series_list, max_lag=10.0)

    assert mat.shape == (5, 5)
    # Diagonal is 1.0
    for i in range(5):
        assert abs(mat[i, i] - 1.0) < 1e-5
    # Symmetry
    assert np.allclose(mat, mat.T, atol=1e-6)
    # Range
    assert np.all(mat >= 0.0) and np.all(mat <= 1.0)
