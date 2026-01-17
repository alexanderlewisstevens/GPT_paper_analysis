# External Connections

This repo avoids hidden dependencies. All external connections are explicit.

## Dataset
- Default location: `data/Classifying_Bipartite_Networks`
- Override with: `DATASET_ROOT=/path/to/clone`
- Bootstrap: `./scripts/bootstrap_data.sh`

## Third-party code
- Stored under `third_party/` with `ATTRIBUTION.md` per dependency.
- Licenses must be included in each folder.

## Companion paper repo
- Expected sibling path: `../GPT_paper`
- No runtime dependency; references are for documentation only.
