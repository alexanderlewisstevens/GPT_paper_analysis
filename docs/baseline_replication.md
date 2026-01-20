# Baseline Replication (R)

This runbook recreates the authors' baseline analysis and PCA figures using
their original R scripts in `data/Classifying_Bipartite_Networks/Code`.

## Prerequisites

- R installed locally (Rscript available on PATH).
- R packages used by the original code:
  - `bipartite`, `igraph`, `tidyverse`, `stringr`, `magrittr`, `glue`,
    `assertthat`, `parallel`, `scales`

## Run

From the repo root:

```bash
./scripts/run_baseline_replication.sh
```

Optional parameters:

```bash
MAX_SIZE=1000 OVERWRITE=FALSE ./scripts/run_baseline_replication.sh
```

Optional flags:

```bash
# Run the heavy simple demo analysis (can be slow and memory intensive)
RUN_SIMPLE_DEMO=TRUE ./scripts/run_baseline_replication.sh

# Skip table generation
RUN_TABLES=FALSE ./scripts/run_baseline_replication.sh
```

## Outputs

- Results CSVs: `data/Classifying_Bipartite_Networks/Results/`
- PCA figures: `data/Classifying_Bipartite_Networks/Figures/`

## Notes

- The plotting script writes figures to `Figures/` relative to the dataset repo.
- If you need different output locations, copy the files into `outputs/` after
  the run.
- `tables.R` writes to `Results/` and `results/` paths; on case-sensitive
  filesystems you may need to adjust the script or create a symlink.
