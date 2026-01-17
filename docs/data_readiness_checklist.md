# Data Readiness Checklist

This checklist keeps data access and split generation reproducible.

## Current Snapshot
- Dataset clone present: `data/Classifying_Bipartite_Networks`.
- Dataset index built: `data/dataset_index.csv`.
- Missing files: `Davidson1989` (ecologicalinteractions).
- Filename collisions: detected on case-insensitive filesystem
  (e.g., Herrera1988, Percival1974, Petanidou1991).
- Splits generated in `data/splits/`:
  - ecological_vs_non_paper
  - ecological_vs_non_all
  - mutualism_vs_antagonism
  - interaction_subtype
- Pilot split created: `data/splits/pilot_mutualism_vs_antagonism.csv`
- Pilot curvature run: 97 processed, 3 skipped (max edges=1000).
- Pilot GCS run: 36 processed before 120s timeout (max edges=1000).
- Pilot config recorded: `configs/pilot_run.yaml`
- Pilot GCS config recorded: `configs/pilot_run_gcs.yaml`
- Pilot log entry: `logs/experiment_log.csv`
- Case-sensitive mount: recommended if you need colliding files.

## Checks (Do in order)
- [ ] Confirm dataset clone is up to date (run `scripts/bootstrap_data.sh`).
- [ ] Rebuild index (run `scripts/run_pipeline.sh`).
- [ ] Resolve missing edgelists or document exceptions.
- [ ] Review split label counts for class balance.
- [ ] Decide pilot subset (label-balanced vs random sample).
- [ ] Record pilot constraints (max edges, max networks).

## Pilot Plan (Proposed Defaults)
- Task: `mutualism_vs_antagonism` (ecological only, 2-class).
- Sample: 50 networks per label (if available).
- Max edges: 1000 (adjust after runtime check).
- Output: `data/features/curvature_features.csv` (generated, ignored).
- Pilot split: `data/splits/pilot_mutualism_vs_antagonism.csv`

## Pilot Split Script
Create a pilot subset from the main split:
```
python3 scripts/build_pilot_split.py
```

See `docs/step_by_step_runbook.md` for the full pilot workflow.

## Notes
- Keep all generated features in `data/features/` (ignored by git).
- Use `DATASET_ROOT` if you move the dataset clone.
