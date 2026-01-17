#!/usr/bin/env python3
import argparse
import csv
import random
from collections import Counter, defaultdict


def main():
    parser = argparse.ArgumentParser(description="Create a pilot split by sampling per label.")
    parser.add_argument(
        "--input-split",
        default="data/splits/mutualism_vs_antagonism_split.csv",
        help="Source split CSV",
    )
    parser.add_argument(
        "--output",
        default="data/splits/pilot_mutualism_vs_antagonism.csv",
        help="Output pilot split CSV",
    )
    parser.add_argument("--per-label", type=int, default=50, help="Max items per label")
    parser.add_argument("--seed", type=int, default=7, help="Random seed")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    with open(args.input_split, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    by_label = defaultdict(list)
    for row in rows:
        by_label[row.get("label", "")].append(row)

    selected = []
    for label, items in sorted(by_label.items()):
        rng.shuffle(items)
        keep = items[: args.per_label]
        selected.extend(keep)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(selected)

    label_counts = Counter(row.get("label", "") for row in selected)
    split_counts = Counter(row.get("split", "") for row in selected)
    print("pilot rows", len(selected))
    print("labels", dict(label_counts))
    print("splits", dict(split_counts))


if __name__ == "__main__":
    main()
