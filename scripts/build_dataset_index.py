#!/usr/bin/env python3
import argparse
import csv
import os
from collections import defaultdict


def normalize_key(value):
    return "".join(ch for ch in value if ch.isalnum()).lower()


def build_file_index(edgelist_root, repo_root):
    index = defaultdict(list)
    normalized_index = defaultdict(list)
    for root, _, files in os.walk(edgelist_root):
        for filename in files:
            if not filename.endswith(".csv"):
                continue
            base = filename[:-4]
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, repo_root)
            index[base].append(rel_path)
            normalized_index[normalize_key(base)].append(rel_path)
    return index, normalized_index


def infer_interaction_fields(row):
    interaction_type = ""
    interaction_subtype = ""
    if row.get("feature_1_name", "").lower() == "interactiontype":
        interaction_type = row.get("feature_1", "")
    if row.get("feature_2_name", "").lower() == "interactionsubtype":
        interaction_subtype = row.get("feature_2", "")
    return interaction_type, interaction_subtype


def main():
    parser = argparse.ArgumentParser(description="Build dataset index from Metadata.csv.")
    parser.add_argument(
        "--metadata",
        default="data/cs_mount/Classifying_Bipartite_Networks/Data/Metadata.csv",
        help="Path to Metadata.csv",
    )
    parser.add_argument(
        "--edgelists",
        default="data/cs_mount/Classifying_Bipartite_Networks/Data/edgelists",
        help="Root directory of empirical edgelists",
    )
    parser.add_argument(
        "--repo-root",
        default=os.getcwd(),
        help="Repository root used to compute relative paths",
    )
    parser.add_argument(
        "--output",
        default="data/dataset_index.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    repo_root = os.path.abspath(args.repo_root)
    edgelist_root = os.path.abspath(args.edgelists)

    file_index, normalized_index = build_file_index(edgelist_root, repo_root)

    with open(args.metadata, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    output_rows = []
    status_counts = defaultdict(int)

    for row in rows:
        name = row.get("name", "")
        network_type = row.get("type", "")
        interaction_type, interaction_subtype = infer_interaction_fields(row)

        expected = os.path.join(edgelist_root, network_type, f"{name}.csv")
        expected_rel = os.path.relpath(expected, repo_root)

        if os.path.exists(expected):
            file_paths = expected_rel
            path_status = "ok"
        else:
            matches = file_index.get(name, [])
            if len(matches) == 1:
                file_paths = matches[0]
                path_status = "matched_other_type"
            elif len(matches) > 1:
                file_paths = ";".join(matches)
                path_status = "ambiguous"
            else:
                norm_matches = normalized_index.get(normalize_key(name), [])
                if len(norm_matches) == 1:
                    file_paths = norm_matches[0]
                    path_status = "normalized_match"
                elif len(norm_matches) > 1:
                    file_paths = ";".join(norm_matches)
                    path_status = "normalized_ambiguous"
                else:
                    file_paths = ""
                    path_status = "missing"

        status_counts[path_status] += 1

        output_rows.append(
            {
                "name": name,
                "type": network_type,
                "interaction_type": interaction_type,
                "interaction_subtype": interaction_subtype,
                "nlinks": row.get("nlinks", ""),
                "connectance": row.get("connectance", ""),
                "nrows": row.get("nrows", ""),
                "ncols": row.get("ncols", ""),
                "file_path": file_paths,
                "path_status": path_status,
            }
        )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "type",
                "interaction_type",
                "interaction_subtype",
                "nlinks",
                "connectance",
                "nrows",
                "ncols",
                "file_path",
                "path_status",
            ],
        )
        writer.writeheader()
        writer.writerows(output_rows)

    print("dataset_index written to", args.output)
    for status, count in sorted(status_counts.items()):
        print(f"{status}: {count}")


if __name__ == "__main__":
    main()
