#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${R_LIBS_USER:-}" ]]; then
  export R_LIBS_USER="${HOME}/Library/R/4.5/library"
fi

DATASET_ROOT="${DATASET_ROOT:-data/Classifying_Bipartite_Networks}"
ANALYSIS_DIR="${DATASET_ROOT}/Code/Analysis"
PLOTTING_DIR="${DATASET_ROOT}/Code/Plotting"
RESULTS_DIR="${DATASET_ROOT}/Results"
FIGURES_DIR="${DATASET_ROOT}/Figures"

MAX_SIZE="${MAX_SIZE:-100}"
OVERWRITE="${OVERWRITE:-FALSE}"
RUN_SIMPLE_DEMO="${RUN_SIMPLE_DEMO:-FALSE}"
RUN_TABLES="${RUN_TABLES:-TRUE}"

if [[ ! -d "${ANALYSIS_DIR}" ]]; then
  echo "Missing analysis directory: ${ANALYSIS_DIR}" >&2
  exit 1
fi

mkdir -p "${RESULTS_DIR}" "${FIGURES_DIR}"

if [[ "${RUN_SIMPLE_DEMO}" == "TRUE" ]]; then
  echo "Running simple demonstration analysis (R) ..."
  (cd "${ANALYSIS_DIR}" && Rscript run_simple_demonstration_analysis.R)
fi

echo "Running full baseline analysis (R) ..."
(cd "${ANALYSIS_DIR}" && Rscript run_full_analysis_over_all_files.R "../../Results/" "${MAX_SIZE}" "${OVERWRITE}")

if [[ "${RUN_TABLES}" == "TRUE" ]]; then
  echo "Generating baseline tables (R) ..."
  (cd "${ANALYSIS_DIR}" && Rscript tables.R)
fi

echo "Generating baseline PCA figures (R) ..."
(cd "${PLOTTING_DIR}" && Rscript plot_pca_simple_demonstration.R)
(cd "${PLOTTING_DIR}" && Rscript plot_pca_results.R)

echo "Baseline replication complete."
echo "Results: ${RESULTS_DIR}"
echo "Figures: ${FIGURES_DIR}"
