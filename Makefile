# Makefile for Kerala Climate Network — Vyuham Pipeline

.PHONY: all data grid events es network robustness landslide export test clean

all: data grid events es network robustness landslide export

data:
	python pipeline/01_download_data.py

grid:
	python pipeline/02_build_grid.py

events:
	python pipeline/03_extract_events.py

es:
	python pipeline/04_sync_matrix.py

network:
	python pipeline/05_build_network.py

robustness:
	python pipeline/06_robustness_study.py

landslide:
	python pipeline/07_landslide_validation.py

export:
	python pipeline/08_export_ui.py

test:
	pytest tests/ -v

clean:
	rm -rf data/interim/* data/processed/* web/public/data/*
