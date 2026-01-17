#!/usr/bin/env python3
import argparse
import csv
import os
import sys
from collections import defaultdict


def percentile(sorted_vals, q):
    if not sorted_vals:
        return None
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    pos = q * (n - 1)
    lower = int(pos)
    upper = min(lower + 1, n - 1)
    if lower == upper:
        return sorted_vals[lower]
    weight = pos - lower
    return sorted_vals[lower] * (1 - weight) + sorted_vals[upper] * weight


def summarize(values, prefix):
    if not values:
        return {
            f"{prefix}_count": 0,
            f"{prefix}_mean": "",
            f"{prefix}_std": "",
            f"{prefix}_min": "",
            f"{prefix}_max": "",
            f"{prefix}_q05": "",
            f"{prefix}_q50": "",
            f"{prefix}_q95": "",
            f"{prefix}_neg_frac": "",
        }
    vals = sorted(values)
    n = len(vals)
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / n
    std = var ** 0.5
    neg_frac = sum(1 for v in vals if v < 0) / n
    return {
        f"{prefix}_count": n,
        f"{prefix}_mean": round(mean, 6),
        f"{prefix}_std": round(std, 6),
        f"{prefix}_min": round(vals[0], 6),
        f"{prefix}_max": round(vals[-1], 6),
        f"{prefix}_q05": round(percentile(vals, 0.05), 6),
        f"{prefix}_q50": round(percentile(vals, 0.50), 6),
        f"{prefix}_q95": round(percentile(vals, 0.95), 6),
        f"{prefix}_neg_frac": round(neg_frac, 6),
    }


def load_edgelist(path, use_weights):
    try:
        import networkx as nx
    except ImportError:
        print("networkx is required. Install with: pip install networkx", file=sys.stderr)
        sys.exit(1)

    g = nx.Graph()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue
            u, v = row[0], row[1]
            if use_weights and len(row) >= 3:
                try:
                    w = float(row[2])
                except ValueError:
                    w = 1.0
                g.add_edge(u, v, weight=w)
            else:
                g.add_edge(u, v)
    return g


def compute_curvatures(g, alpha):
    try:
        from GraphRicciCurvature.OllivierRicci import OllivierRicci
        from GraphRicciCurvature.FormanRicci import FormanRicci
    except ImportError:
        print(
            "GraphRicciCurvature is required. Install with: pip install GraphRicciCurvature",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        import networkx as nx
    except ImportError:
        print("networkx is required. Install with: pip install networkx", file=sys.stderr)
        sys.exit(1)

    # GraphRicciCurvature relies on networkit, which requires contiguous integer nodes.
    g_int = nx.convert_node_labels_to_integers(g, first_label=0, ordering="default")

    orc = OllivierRicci(g_int, alpha=alpha, verbose="ERROR")
    orc.compute_ricci_curvature()
    orc_graph = orc.G
    orc_values = [
        data.get("ricciCurvature")
        for _, _, data in orc_graph.edges(data=True)
        if data.get("ricciCurvature") is not None
    ]

    frc = FormanRicci(g_int)
    frc.compute_ricci_curvature()
    frc_graph = frc.G
    frc_values = [
        data.get("formanCurvature")
        for _, _, data in frc_graph.edges(data=True)
        if data.get("formanCurvature") is not None
    ]

    return orc_values, frc_values


def main():
    parser = argparse.ArgumentParser(description="Compute curvature features for networks.")
    parser.add_argument(
        "--dataset-index",
        default="data/dataset_index.csv",
        help="Dataset index CSV with file paths",
    )
    parser.add_argument(
        "--split",
        default="",
        help="Optional split CSV to filter networks",
    )
    parser.add_argument(
        "--split-set",
        default="",
        help="Optional split set to filter (train/test)",
    )
    parser.add_argument(
        "--output",
        default="data/features/curvature_features.csv",
        help="Output CSV path",
    )
    parser.add_argument("--alpha", type=float, default=0.5, help="Ollivier alpha")
    parser.add_argument(
        "--use-weights",
        action="store_true",
        help="Use weights if provided in edgelists",
    )
    parser.add_argument(
        "--max-edges",
        type=int,
        default=0,
        help="Skip networks with more than this many edges (0=disable)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of networks processed (0=disable)",
    )
    args = parser.parse_args()

    split_filter = {}
    if args.split:
        with open(args.split, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if args.split_set and row.get("split") != args.split_set:
                    continue
                split_filter[row.get("name", "")] = row

    with open(args.dataset_index, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        index_rows = list(reader)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    output_fields = [
        "name",
        "type",
        "interaction_type",
        "interaction_subtype",
        "node_count",
        "edge_count",
        "orc_count",
        "orc_mean",
        "orc_std",
        "orc_min",
        "orc_max",
        "orc_q05",
        "orc_q50",
        "orc_q95",
        "orc_neg_frac",
        "frc_count",
        "frc_mean",
        "frc_std",
        "frc_min",
        "frc_max",
        "frc_q05",
        "frc_q50",
        "frc_q95",
        "frc_neg_frac",
    ]

    processed = 0
    skipped = defaultdict(int)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()

        for row in index_rows:
            name = row.get("name", "")
            if split_filter and name not in split_filter:
                continue
            if row.get("path_status") in {"missing", "ambiguous", "normalized_ambiguous"}:
                skipped["missing_path"] += 1
                continue
            path = row.get("file_path", "")
            if not path or not os.path.exists(path):
                skipped["missing_path"] += 1
                continue

            g = load_edgelist(path, args.use_weights)
            edge_count = g.number_of_edges()
            if args.max_edges and edge_count > args.max_edges:
                skipped["too_large"] += 1
                continue

            try:
                orc_values, frc_values = compute_curvatures(g, args.alpha)
            except Exception as exc:
                skipped["curvature_error"] += 1
                print(f"error computing curvature for {name}: {exc}", file=sys.stderr)
                continue

            features = {
                "name": name,
                "type": row.get("type", ""),
                "interaction_type": row.get("interaction_type", ""),
                "interaction_subtype": row.get("interaction_subtype", ""),
                "node_count": g.number_of_nodes(),
                "edge_count": edge_count,
            }
            features.update(summarize(orc_values, "orc"))
            features.update(summarize(frc_values, "frc"))
            writer.writerow(features)
            processed += 1

            if args.limit and processed >= args.limit:
                break

    print("processed", processed)
    for key, val in skipped.items():
        print(f"skipped_{key}", val)


if __name__ == "__main__":
    main()
