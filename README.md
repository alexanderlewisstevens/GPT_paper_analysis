# GPT Paper Analysis

This repository contains the reproducible analysis pipeline and data tooling for
curvature experiments. It is intentionally decoupled from paper writing.
The companion paper repo lives at `../GPT_paper`.

## Structure
- `scripts/`: data bootstrap, index/split generation, curvature extraction
- `configs/`: run configs (e.g., pilot runs)
- `data/`: local datasets and derived artifacts (ignored by git)
- `outputs/`: model outputs, figures, tables (ignored by git)
- `logs/`: experiment logs (tracked)
- `third_party/`: external code with attribution

## Setup
```
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Data bootstrap
```
./scripts/bootstrap_data.sh
```

## Index + splits
```
./scripts/run_pipeline.sh
```

## Pilot split
```
python3 scripts/build_pilot_split.py
```

## Curvature features (pilot)
```
python3 scripts/compute_curvature_features.py \
  --split data/splits/pilot_mutualism_vs_antagonism.csv \
  --max-edges 1000
```

## Baseline replication (R)

Run the authors' baseline analysis and PCA figures:

```
./scripts/run_baseline_replication.sh
```

See `docs/baseline_replication.md` for details and optional flags.

## Baseline parity (R pipeline)

Run the author R analysis to produce baseline results files, then export a
baseline feature table for merging with curvature.

```
cd data/Classifying_Bipartite_Networks/Code/Analysis
Rscript run_full_analysis_over_all_files.R ../../Results/ 1000 FALSE
cd ../../../..
```

```
python3 scripts/compute_curvature_features.py --max-edges 1000
Rscript scripts/export_baseline_features.R --randomization=empirical
Rscript scripts/merge_baseline_curvature.R
```

## Naming conventions
- Use short, lowercase names with underscores for config files.
- Include run IDs in configs and logs (e.g., `pilot_YYYYMMDD_HHMMSS`).
- Keep generated outputs in `data/` or `outputs/`, not in `configs/`.

## Reproducibility
- Use `DATASET_ROOT` to point at a custom dataset location.
- Third-party code must live under `third_party/` with attribution.
