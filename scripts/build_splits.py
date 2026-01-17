#!/usr/bin/env python3
import argparse
import csv
import os
import random
from collections import Counter, defaultdict


PAPER_NONECO_TYPES = {
    "actorcollaboration",
    "authorship",
    "legislature",
    "microbiome",
    "crimes",
}


def infer_interaction_fields(row):
    interaction_type = ""
    interaction_subtype = ""
    if row.get("feature_1_name", "").lower() == "interactiontype":
        interaction_type = row.get("feature_1", "")
    if row.get("feature_2_name", "").lower() == "interactionsubtype":
        interaction_subtype = row.get("feature_2", "")
    return interaction_type, interaction_subtype


def stratified_split(rows, label_fn, rng, test_fraction):
    by_label = defaultdict(list)
    for row in rows:
        by_label[label_fn(row)].append(row)

    split_rows = []
    warnings = []
    for label, items in by_label.items():
        rng.shuffle(items)
        n_total = len(items)
        n_test = int(round(n_total * test_fraction))
        if n_total <= 1:
            n_test = 0
            warnings.append(f"label {label} has {n_total} item(s); all in train")
        else:
            n_test = max(1, n_test)
            if n_test >= n_total:
                n_test = n_total - 1
                warnings.append(f"label {label} small; reduced test size to {n_test}")

        test_items = items[:n_test]
        train_items = items[n_test:]

        for row in train_items:
            split_rows.append((row, label, "train"))
        for row in test_items:
            split_rows.append((row, label, "test"))

    return split_rows, warnings


def write_split_csv(output_path, split_rows, task_name):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "split",
                "label",
                "task",
                "type",
                "interaction_type",
                "interaction_subtype",
            ],
        )
        writer.writeheader()
        for row, label, split in split_rows:
            writer.writerow(
                {
                    "name": row.get("name", ""),
                    "split": split,
                    "label": label,
                    "task": task_name,
                    "type": row.get("type", ""),
                    "interaction_type": row.get("interaction_type", ""),
                    "interaction_subtype": row.get("interaction_subtype", ""),
                }
            )


def main():
    parser = argparse.ArgumentParser(description="Create train/test splits from Metadata.csv.")
    parser.add_argument(
        "--metadata",
        default="data/cs_mount/Classifying_Bipartite_Networks/Data/Metadata.csv",
        help="Path to Metadata.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="data/splits",
        help="Directory for output split CSVs",
    )
    parser.add_argument("--seed", type=int, default=7, help="Random seed")
    parser.add_argument("--test-fraction", type=float, default=0.2, help="Test fraction")
    parser.add_argument(
        "--min-class-size",
        type=int,
        default=10,
        help="Minimum class size for interaction_subtype task",
    )
    args = parser.parse_args()

    rng = random.Random(args.seed)

    with open(args.metadata, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        interaction_type, interaction_subtype = infer_interaction_fields(row)
        row["interaction_type"] = interaction_type
        row["interaction_subtype"] = interaction_subtype

    tasks = []

    # Task 1: Ecological vs nonecological (paper categories only)
    def paper_filter(row):
        return row.get("type") in PAPER_NONECO_TYPES or row.get("type") == "ecologicalinteractions"

    def eco_label(row):
        return "ecological" if row.get("type") == "ecologicalinteractions" else "nonecological"

    tasks.append(("ecological_vs_non_paper", paper_filter, eco_label))

    # Task 2: Ecological vs nonecological (all types)
    tasks.append(("ecological_vs_non_all", lambda r: True, eco_label))

    # Task 3: Mutualism vs antagonism
    def eco_filter(row):
        return row.get("type") == "ecologicalinteractions"

    def mutualism_antagonism_filter(row):
        return eco_filter(row) and row.get("interaction_type") in {"mutualism", "antagonism"}

    tasks.append(("mutualism_vs_antagonism", mutualism_antagonism_filter, lambda r: r.get("interaction_type", "")))

    # Task 4: Interaction subtype (filtered by min class size)
    subtype_rows = [r for r in rows if eco_filter(r) and r.get("interaction_subtype") not in {"", "NA"}]
    subtype_counts = Counter(r.get("interaction_subtype", "") for r in subtype_rows)
    keep_subtypes = {k for k, v in subtype_counts.items() if v >= args.min_class_size}

    def subtype_filter(row):
        return (
            eco_filter(row)
            and row.get("interaction_subtype") in keep_subtypes
        )

    tasks.append(("interaction_subtype", subtype_filter, lambda r: r.get("interaction_subtype", "")))

    print("Preparing splits with seed", args.seed, "and test_fraction", args.test_fraction)

    for task_name, task_filter, label_fn in tasks:
        task_rows = [r for r in rows if task_filter(r)]
        split_rows, warnings = stratified_split(task_rows, label_fn, rng, args.test_fraction)
        output_path = os.path.join(args.output_dir, f"{task_name}_split.csv")
        write_split_csv(output_path, split_rows, task_name)

        label_counts = Counter(label_fn(r) for r in task_rows)
        print(f"task {task_name}: {len(task_rows)} rows, labels {dict(label_counts)}")
        for warning in warnings:
            print("warning:", warning)


if __name__ == "__main__":
    main()
