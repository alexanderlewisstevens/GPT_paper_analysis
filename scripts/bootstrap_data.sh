#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/mjsmith037/Classifying_Bipartite_Networks"
TARGET_DIR="data/Classifying_Bipartite_Networks"

if [[ -d "${TARGET_DIR}/.git" ]]; then
  echo "Dataset repo already present at ${TARGET_DIR}"
  exit 0
fi

if [[ -e "${TARGET_DIR}" ]]; then
  echo "Target exists but is not a git repo: ${TARGET_DIR}" >&2
  echo "Move it aside or delete it, then re-run." >&2
  exit 1
fi

mkdir -p "data"
git clone --depth 1 "${REPO_URL}" "${TARGET_DIR}"

echo "Clone complete."
echo "If you need a case-sensitive volume, see data/case_sensitive_volume.md"
