#!/usr/bin/env python3
import argparse
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path


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


def load_edgelist(path):
    edges = []
    nodes = set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue
            u, v = row[0], row[1]
            nodes.add(u)
            nodes.add(v)
            edges.append((u, v))
    return nodes, edges


def build_adjacency(nodes, edges):
    node_list = sorted(nodes)
    idx = {node: i for i, node in enumerate(node_list)}
    n = len(node_list)
    A = [[0 for _ in range(n)] for _ in range(n)]
    edge_pairs = set()
    for u, v in edges:
        i = idx[u]
        j = idx[v]
        if i == j:
            continue
        if i > j:
            i, j = j, i
        if (i, j) in edge_pairs:
            continue
        edge_pairs.add((i, j))
        A[i][j] = 1
        A[j][i] = 1
    return A, node_list, sorted(edge_pairs)


def load_gcs_modules():
    root = Path(__file__).resolve().parents[1] / "third_party" / "graph-curvature-server"
    sys.path.insert(0, str(root))
    try:
        import types

        if "web" not in sys.modules:
            web_stub = types.SimpleNamespace()
            web_stub.config = types.SimpleNamespace(debug=False)
            sys.modules["web"] = web_stub
        import curvature as gcs_curv
        import graph as gcs_graph
    finally:
        if sys.path[0] == str(root):
            sys.path.pop(0)
    return gcs_curv, gcs_graph


def compute_edge_curvatures(edge_pairs, A, gcs_graph, idleness, compute_flags):
    results = {}
    if compute_flags.get("orc"):
        results["orc"] = [gcs_graph.ocurve(i, j, A) for i, j in edge_pairs]
    if compute_flags.get("orc_idl"):
        results["orc_idl"] = [gcs_graph.lazocurve(i, j, A, idleness) for i, j in edge_pairs]
    if compute_flags.get("lly"):
        results["lly"] = [gcs_graph.LLYcurv(i, j, A) for i, j in edge_pairs]
    if compute_flags.get("nnlly"):
        results["nnlly"] = [gcs_graph.nonnorm_ocurve(i, j, A) for i, j in edge_pairs]
    return results


def compute_vertex_curvatures(A, gcs_curv, compute_flags, bakry_dim):
    results = {}
    if compute_flags.get("be_non_norm"):
        results["be_non_norm"] = gcs_curv.non_normalised_unweighted_curvature(A, gcs_curv.inf)
    if compute_flags.get("be_norm"):
        results["be_norm"] = gcs_curv.normalised_unweighted_curvature(A, gcs_curv.inf)
    if compute_flags.get("be_non_norm_dim") and bakry_dim:
        results["be_non_norm_dim"] = gcs_curv.non_normalised_unweighted_curvature(A, bakry_dim)
    if compute_flags.get("be_norm_dim") and bakry_dim:
        results["be_norm_dim"] = gcs_curv.normalised_unweighted_curvature(A, bakry_dim)
    if compute_flags.get("steiner"):
        results["steiner"] = gcs_curv.steinerbergerCurvature(A)
    if compute_flags.get("node_res"):
        results["node_res"] = gcs_curv.nodeResistanceCurvature(A)
    return results


def compute_link_resistance(edge_pairs, A, gcs_curv):
    lrc = gcs_curv.linkResistanceCurvature(A)
    return [lrc[i][j] for i, j in edge_pairs]


def main():
    parser = argparse.ArgumentParser(
        description="Compute curvature features using graph-curvature-server backend."
    )
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
        default="data/features/curvature_features_gcs.csv",
        help="Output CSV path",
    )
    parser.add_argument("--idleness", type=float, default=0.5, help="Ollivier idleness")
    parser.add_argument(
        "--bakry-dimension",
        type=float,
        default=0.0,
        help="Finite dimension N for Bakry-Emery (0=skip finite N)",
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
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include slower edge-based measures (Ollivier/LLY).",
    )
    parser.add_argument(
        "--no-ollivier",
        action="store_true",
        help="Skip Ollivier-Ricci (only relevant with --full).",
    )
    parser.add_argument(
        "--no-lly",
        action="store_true",
        help="Skip Lin-Lu-Yau (only relevant with --full).",
    )
    parser.add_argument("--no-bakry", action="store_true", help="Skip Bakry-Emery")
    parser.add_argument("--with-steiner", action="store_true", help="Include Steinerberger")
    parser.add_argument("--with-resistance", action="store_true", help="Include resistance curvature")
    parser.add_argument(
        "--with-ollivier-idleness",
        action="store_true",
        help="Include lazy Ollivier-Ricci curvature (slow, requires --full).",
    )
    parser.add_argument(
        "--with-nonnorm-lly",
        action="store_true",
        help="Include non-normalised Lin-Lu-Yau curvature (slow, requires --full).",
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

    include_ollivier = args.full and not args.no_ollivier
    include_lly = args.full and not args.no_lly
    compute_flags = {
        "orc": include_ollivier,
        "orc_idl": include_ollivier and args.with_ollivier_idleness,
        "lly": include_lly,
        "nnlly": include_lly and args.with_nonnorm_lly,
        "be_non_norm": not args.no_bakry,
        "be_norm": not args.no_bakry,
        "be_non_norm_dim": not args.no_bakry and args.bakry_dimension,
        "be_norm_dim": not args.no_bakry and args.bakry_dimension,
        "steiner": args.with_steiner,
        "node_res": args.with_resistance,
    }
    compute_link_res = args.with_resistance

    gcs_curv, gcs_graph = load_gcs_modules()

    output_fields = [
        "name",
        "type",
        "interaction_type",
        "interaction_subtype",
        "node_count",
        "edge_count",
    ]

    prefix_order = [
        ("orc", "edge"),
        ("orc_idl", "edge"),
        ("lly", "edge"),
        ("nnlly", "edge"),
        ("be_non_norm", "node"),
        ("be_norm", "node"),
        ("be_non_norm_dim", "node"),
        ("be_norm_dim", "node"),
        ("steiner", "node"),
        ("node_res", "node"),
        ("link_res", "edge"),
    ]

    for prefix, _ in prefix_order:
        if prefix == "link_res" and not compute_link_res:
            continue
        if not compute_flags.get(prefix, False) and prefix != "link_res":
            continue
        output_fields.extend(
            [
                f"{prefix}_count",
                f"{prefix}_mean",
                f"{prefix}_std",
                f"{prefix}_min",
                f"{prefix}_max",
                f"{prefix}_q05",
                f"{prefix}_q50",
                f"{prefix}_q95",
                f"{prefix}_neg_frac",
            ]
        )

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

            nodes, edges = load_edgelist(path)
            edge_count = len(edges)
            if args.max_edges and edge_count > args.max_edges:
                skipped["too_large"] += 1
                continue

            if not nodes:
                skipped["empty"] += 1
                continue

            try:
                A, node_list, edge_pairs = build_adjacency(nodes, edges)
                edge_curv = compute_edge_curvatures(edge_pairs, A, gcs_graph, args.idleness, compute_flags)
                vertex_curv = compute_vertex_curvatures(A, gcs_curv, compute_flags, args.bakry_dimension)
                if compute_link_res:
                    edge_curv["link_res"] = compute_link_resistance(edge_pairs, A, gcs_curv)
            except Exception as exc:
                skipped["curvature_error"] += 1
                print(f"error computing curvature for {name}: {exc}", file=sys.stderr)
                continue

            features = {
                "name": name,
                "type": row.get("type", ""),
                "interaction_type": row.get("interaction_type", ""),
                "interaction_subtype": row.get("interaction_subtype", ""),
                "node_count": len(node_list),
                "edge_count": len(edge_pairs),
            }

            for prefix, _ in prefix_order:
                if prefix == "link_res" and not compute_link_res:
                    continue
                if prefix in edge_curv:
                    features.update(summarize(edge_curv[prefix], prefix))
                elif prefix in vertex_curv:
                    features.update(summarize(vertex_curv[prefix], prefix))

            writer.writerow(features)
            processed += 1

            if args.limit and processed >= args.limit:
                break

    print("processed", processed)
    for key, val in skipped.items():
        print(f"skipped_{key}", val)


if __name__ == "__main__":
    main()
