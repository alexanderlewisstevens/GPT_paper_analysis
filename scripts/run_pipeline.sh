#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
DATASET_ROOT="${DATASET_ROOT:-data/Classifying_Bipartite_Networks}"

METADATA_PATH="${DATASET_ROOT}/Data/Metadata.csv"
EDGELIST_ROOT="${DATASET_ROOT}/Data/edgelists"

if [[ ! -f "${METADATA_PATH}" ]]; then
  echo "Missing Metadata.csv at ${METADATA_PATH}" >&2
  echo "Run scripts/bootstrap_data.sh or set DATASET_ROOT to your dataset clone." >&2
  exit 1
fi

${PYTHON_BIN} scripts/build_dataset_index.py \
  --metadata "${METADATA_PATH}" \
  --edgelists "${EDGELIST_ROOT}" \
  --output "data/dataset_index.csv"

${PYTHON_BIN} scripts/build_splits.py \
  --metadata "${METADATA_PATH}" \
  --output-dir "data/splits"

echo "Index + splits complete."
echo "Curvature extraction is intentionally not run."
echo "When ready, run:"
echo "  ${PYTHON_BIN} scripts/compute_curvature_features.py --max-edges 2000"
