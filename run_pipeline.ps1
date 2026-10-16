# PowerShell runner for Kerala Climate Network (Vyuham)
param (
    [string]$Stage = "all"
)

$ErrorActionPreference = "Stop"

function Run-Stage1 { python pipeline/01_download_data.py }
function Run-Stage2 { python pipeline/02_build_grid.py }
function Run-Stage3 { python pipeline/03_extract_events.py }
function Run-Stage4 { python pipeline/04_sync_matrix.py }
function Run-Stage5 { python pipeline/05_build_network.py }
function Run-Stage6 { python pipeline/06_robustness_study.py }
function Run-Stage7 { python pipeline/07_landslide_validation.py }
function Run-Stage8 { python pipeline/08_export_ui.py }

Write-Host ">>> Executing pipeline stage: $Stage" -ForegroundColor Cyan

switch ($Stage.ToLower()) {
    "data" { Run-Stage1 }
    "grid" { Run-Stage2 }
    "events" { Run-Stage3 }
    "es" { Run-Stage4 }
    "network" { Run-Stage5 }
    "robustness" { Run-Stage6 }
    "landslide" { Run-Stage7 }
    "export" { Run-Stage8 }
    "test" { pytest tests/ -v }
    "all" {
        Run-Stage1
        Run-Stage2
        Run-Stage3
        Run-Stage4
        Run-Stage5
        Run-Stage6
        Run-Stage7
        Run-Stage8
        Write-Host ">>> Pipeline executed successfully!" -ForegroundColor Green
    }
    default {
        Write-Host "Unknown stage: $Stage. Valid options: data, grid, events, es, network, robustness, landslide, export, test, all" -ForegroundColor Yellow
    }
}
