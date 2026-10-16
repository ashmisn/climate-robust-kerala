"""
sync.py - Event Synchronization (Quian Quiroga et al. 2002).
High-performance numba implementation of dynamic lag symmetric score Q_ij.
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from numba import njit, prange

@njit(fastmath=True)
def pair_event_synchronization(
    ti: np.ndarray,
    tj: np.ndarray,
    max_lag: float = 10.0
) -> float:
    """
    Computes symmetric normalized Event Synchronization score Q_ij
    between two event series ti and tj according to Quian Quiroga et al. (2002).
    """
    ni = len(ti)
    nj = len(tj)

    if ni < 2 or nj < 2:
        return 0.0

    # Precompute intra-series intervals for series i
    diff_i = np.zeros(ni, dtype=np.float64)
    diff_i[0] = ti[1] - ti[0]
    diff_i[-1] = ti[-1] - ti[-2]
    for l in range(1, ni - 1):
        diff_i[l] = min(ti[l] - ti[l - 1], ti[l + 1] - ti[l])

    # Precompute intra-series intervals for series j
    diff_j = np.zeros(nj, dtype=np.float64)
    diff_j[0] = tj[1] - tj[0]
    diff_j[-1] = tj[-1] - tj[-2]
    for m in range(1, nj - 1):
        diff_j[m] = min(tj[m] - tj[m - 1], tj[m + 1] - tj[m])

    c_ij = 0.0
    c_ji = 0.0

    m_start = 0
    for l in range(ni):
        t_l = ti[l]
        d_i = diff_i[l]

        # Advance m_start pointer since series are sorted
        while m_start < nj and tj[m_start] < (t_l - max_lag):
            m_start += 1

        for m in range(m_start, nj):
            t_m = tj[m]
            dt = t_l - t_m

            if dt < -max_lag:
                break  # Beyond upper lag limit

            # Dynamic delay tau
            tau = 0.5 * min(d_i, diff_j[m])
            if tau > max_lag:
                tau = max_lag

            if dt > 0.0 and dt <= tau:
                c_ij += 1.0
            elif dt < 0.0 and (-dt) <= tau:
                c_ji += 1.0
            elif dt == 0.0:
                c_ij += 0.5
                c_ji += 0.5

    denom = np.sqrt(float(ni) * float(nj))
    if denom == 0.0:
        return 0.0

    q = (c_ij + c_ji) / denom
    if q > 1.0:
        q = 1.0
    elif q < 0.0:
        q = 0.0
    return q

def compute_full_es_matrix(
    event_series_list: List[np.ndarray],
    max_lag: float = 10.0
) -> np.ndarray:
    """
    Computes full N x N Event Synchronization matrix Q_ij.
    """
    n = len(event_series_list)
    # Ensure float64 sorted 1D arrays for numba
    preprocessed_events = [np.asarray(s, dtype=np.float64) for s in event_series_list]
    es_matrix = np.zeros((n, n), dtype=np.float32)

    for i in range(n):
        es_matrix[i, i] = 1.0
        ti = preprocessed_events[i]
        for j in range(i + 1, n):
            tj = preprocessed_events[j]
            q = pair_event_synchronization(ti, tj, max_lag=max_lag)
            es_matrix[i, j] = q
            es_matrix[j, i] = q

    return es_matrix
