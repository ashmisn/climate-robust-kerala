# Rules for coding agents

- Read the spec before writing code. Work on ONE stage or page at a time.
- Never invent data or results. If a dataset is missing, stop and say so.
- Every parameter goes in config.yaml. No magic numbers in code.
- Do not change the data contract without updating both the pipeline and the UI.
- Write tests for numerical code. Run them and report the results.
- Run new code on a small subset before the full dataset and report the runtime.
- Keep functions small and typed. No notebooks as source of truth.
- Log data provenance (source, download date, version) to data/raw/PROVENANCE.md.
- After each stage: list files changed, how to run it, and what was verified.
- When uncertain about a scientific choice, ask; do not silently pick one.
