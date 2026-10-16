"""
pipeline/05_build_network.py - Stage 5: Climate Network Construction & Centralities.
Thresholds ES matrix (top 5%), builds undirected weighted graph,
computes degree, betweenness, clustering, and eigenvector centralities.
Outputs: data/processed/network.graphml, data/processed/metrics.parquet
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ktnet.io import load_config
from src.ktnet.network import build_climate_network, compute_network_metrics, save_network_outputs

def main():
    print("=== Stage 5: Climate Network Construction ===")
    config = load_config("config.yaml")

    es_matrix_path = Path(config["paths"]["interim_data_dir"]) / "es_matrix.npy"
    cells_parquet_path = Path(config["paths"]["interim_data_dir"]) / "cells.parquet"
    out_graphml_path = Path(config["paths"]["processed_data_dir"]) / "network.graphml"
    out_metrics_path = Path(config["paths"]["processed_data_dir"]) / "metrics.parquet"

    es_matrix = np.load(es_matrix_path)
    df_cells = pd.read_parquet(cells_parquet_path)
    cell_ids = df_cells["cell_id"].tolist()

    link_fraction = float(config["network"].get("link_fraction", 0.05))
    max_iter = int(config["network"].get("eigenvector_max_iter", 1000))
    tol = float(config["network"].get("eigenvector_tol", 1e-6))

    print(f"Building network with top {link_fraction * 100:.1f}% links across {len(cell_ids)} nodes...")
    G, links_list, cutoff = build_climate_network(es_matrix, cell_ids, link_fraction=link_fraction)
    print(f"Graph nodes: {G.number_of_nodes()}, edges: {G.number_of_edges()}, Q cutoff: {cutoff:.4f}")

    print("Computing degree, betweenness, clustering, and eigenvector centralities...")
    df_metrics = compute_network_metrics(G, cell_ids, max_iter=max_iter, tol=tol)

    print("Top 5 cells by Betweenness Centrality:")
    top_bet = df_metrics.sort_values(by="betweenness", ascending=False).head(5)
    print(top_bet[["cell_id", "betweenness", "degree", "eigenvector"]])

    save_network_outputs(G, df_metrics, str(out_graphml_path), str(out_metrics_path))
    print(f"Stage 5 complete: Saved {out_graphml_path} and {out_metrics_path}")

if __name__ == "__main__":
    main()
