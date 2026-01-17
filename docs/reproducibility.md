# Reproducibility Runbook (Analysis Repo)

## 1) Bootstrap data
```
./scripts/bootstrap_data.sh
```

## 2) Build index + splits
```
./scripts/run_pipeline.sh
```

## 3) Pilot split
```
python3 scripts/build_pilot_split.py
```

## 4) Curvature extraction (pilot)
```
python3 scripts/compute_curvature_features.py \
  --split data/splits/pilot_mutualism_vs_antagonism.csv \
  --max-edges 1000
```

## 5) Curvature extraction (graph-curvature-server backend)
```
python3 scripts/compute_curvature_features_gcs.py \
  --split data/splits/pilot_mutualism_vs_antagonism.csv \
  --max-edges 1000 \
  --output data/features/curvature_features_gcs.csv
```
Defaults to fast node-based Bakry-Emery measures. To include slower edge-based
Ollivier/LLY measures, add `--full` (and optional
`--with-ollivier-idleness` / `--with-nonnorm-lly`).

## Notes
- Use `DATASET_ROOT` to point to a custom dataset clone.
- Third-party code lives under `third_party/` with attribution.
- Logs are tracked in `logs/experiment_log.csv`.
