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

## Notes
- Use `DATASET_ROOT` to point to a custom dataset clone.
- Third-party code lives under `third_party/` with attribution.
- Logs are tracked in `logs/experiment_log.csv`.
