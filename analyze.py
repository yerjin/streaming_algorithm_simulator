#!/usr/bin/env python3
import argparse
from collections import defaultdict
from pathlib import Path

import pandas as pd


ALGORITHMS = [
    "cmsketch",
    "spacesaving",
    "stickysampling",
    "lossycounting",
    "setassociativelfu",
    "setassociativelru",
    "setassociativedrop",
    "countertrie",
]

COLS = ["window", "address", "count"]


def load_threecol_csv(path: Path) -> pd.DataFrame:
    # First line is header
    df = pd.read_csv(path, header=0)  # header row parsing [web:9]

    # Normalize possible column names
    rename_map = {
        "window_idx": "window",
        "window": "window",
        "item": "address",
        "address": "address",
        "est_count": "count",
        "true_count": "count",
        "count": "count",
    }
    df = df.rename(columns=rename_map)

    required = {"window", "address", "count"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"{path}: missing columns {missing}, got {list(df.columns)}")

    df = df[["window", "address", "count"]].copy()
    df["window"] = df["window"].astype(int)
    df["address"] = df["address"].astype(str).str.strip()
    df["count"] = df["count"].astype(int)
    return df


def normalize_oracle(oracle_path: Path) -> pd.DataFrame:
    oracle = load_threecol_csv(oracle_path)
    oracle = oracle.groupby(["window", "address"], as_index=False)["count"].sum()
    oracle = oracle.rename(columns={"count": "true_count"})
    return oracle


def normalize_algo(algo_path: Path) -> pd.DataFrame:
    algo = load_threecol_csv(algo_path)
    algo = algo[["window", "address"]].drop_duplicates()
    return algo


def per_window_metrics(oracle: pd.DataFrame, algo_hot: pd.DataFrame) -> pd.DataFrame:
    """
    Return per-window:
      k, hit, recall@k, algo_true_sum, oracle_topk_sum, access_count_ratio
    """
    k_df = algo_hot.groupby("window", as_index=False).size().rename(columns={"size": "k"})
    if k_df.empty:
        return pd.DataFrame(
            columns=[
                "window",
                "k",
                "hit",
                "recall@k",
                "algo_true_sum",
                "oracle_topk_sum",
                "access_count_ratio",
            ]
        )

    oracle_sorted = oracle.sort_values(["window", "true_count"], ascending=[True, False]).copy()
    oracle_sorted["rank"] = oracle_sorted.groupby("window").cumcount() + 1

    oracle_with_k = oracle_sorted.merge(k_df, on="window", how="inner")  # multi-key merge usage pattern [web:51]
    oracle_topk = oracle_with_k[oracle_with_k["rank"] <= oracle_with_k["k"]][
        ["window", "address", "true_count", "k"]
    ]

    topk_sum = (
        oracle_topk.groupby("window", as_index=False)["true_count"]
        .sum()
        .rename(columns={"true_count": "oracle_topk_sum"})
    )

    algo_join = algo_hot.merge(oracle, on=["window", "address"], how="left")  # join on multiple keys [web:51]
    algo_join["true_count"] = algo_join["true_count"].fillna(0).astype(int)
    algo_true_sum = (
        algo_join.groupby("window", as_index=False)["true_count"]
        .sum()
        .rename(columns={"true_count": "algo_true_sum"})
    )

    hit_df = (
        algo_hot.merge(oracle_topk[["window", "address"]], on=["window", "address"], how="inner")
        .groupby("window", as_index=False)
        .size()
        .rename(columns={"size": "hit"})
    )

    out = (
        k_df.merge(hit_df, on="window", how="left")
        .merge(topk_sum, on="window", how="left")
        .merge(algo_true_sum, on="window", how="left")
    )
    out["hit"] = out["hit"].fillna(0).astype(int)
    out["oracle_topk_sum"] = out["oracle_topk_sum"].fillna(0).astype(int)
    out["algo_true_sum"] = out["algo_true_sum"].fillna(0).astype(int)

    out["recall@k"] = out.apply(lambda r: (r["hit"] / r["k"]) if r["k"] > 0 else 0.0, axis=1)
    out["access_count_ratio"] = out.apply(
        lambda r: (r["algo_true_sum"] / r["oracle_topk_sum"]) if r["oracle_topk_sum"] > 0 else 0.0,
        axis=1,
    )
    return out.sort_values("window").reset_index(drop=True)


def parse_filename(p: Path):
    # <prefix>.<epoch>.<kind>.<resource>.csv
    # kind == 'oracle' OR kind in ALGORITHMS
    name = p.name
    if not name.endswith(".csv"):
        return None
    stem = name[:-4]
    parts = stem.split(".")
    if len(parts) < 4:
        return None

    
    
    resource_str = parts[-1]
    if not resource_str.isdigit():   # NEW: ignore report/other non-numeric suffix
        return None

    resource = int(parts[-1])

    kind = parts[-2]
    epoch = parts[-3]
    prefix = ".".join(parts[:-3])
    return prefix, epoch, kind, resource


def discover_single_group(root: Path, expected_prefix: str):
    """
    Your directory has only one (prefix, epoch) pair.
    We discover:
      - oracle_path: <prefix>.<epoch>.oracle.0.csv
      - algo_paths: dict[(algo, resource)] = path
    """
    oracle_path = None
    algo_paths = {}  # (algo, resource) -> Path
    seen_groups = set()

    for p in root.glob("*.csv"):
        parsed = parse_filename(p)
        if not parsed:
            continue
        prefix, epoch, kind, resource = parsed

        if prefix != expected_prefix:   # NEW: prefix mismatch skip
            continue

        seen_groups.add((prefix, epoch))

        if kind == "oracle":
            if resource != 0:
                raise RuntimeError(f"Oracle resource must be 0, got {p}")
            if oracle_path is not None and oracle_path != p:
                raise RuntimeError(f"Multiple oracle files found: {oracle_path}, {p}")
            oracle_path = p
            continue

        if kind in ALGORITHMS:
            algo_paths[(kind, resource)] = p

    if not seen_groups:
        raise RuntimeError(f"No matching CSV files found in {root}")

    if len(seen_groups) != 1:
        raise RuntimeError(f"Expected single (prefix,epoch) in dir, found: {sorted(seen_groups)}")

    (prefix, epoch) = next(iter(seen_groups))
    if oracle_path is None:
        raise RuntimeError(f"Oracle file not found for (prefix,epoch)=({prefix},{epoch}) in {root}")

    return prefix, epoch, oracle_path, algo_paths


def col_sort_key(col: str):
    # col: "cmsketch.16384"
    algo, res = col.rsplit(".", 1)
    algo_idx = ALGORITHMS.index(algo) if algo in ALGORITHMS else 10**9
    return (algo_idx, int(res))


def build_report(root: Path, expected_prefix: str) -> Path:
    prefix, epoch, oracle_path, algo_paths = discover_single_group(root, expected_prefix)

    oracle = normalize_oracle(oracle_path)

    # report: rows are metrics, columns are algo.resource
    metrics = ["num_windows", "avg_k", "avg_recall@k", "avg_access_count_ratio"]
    report = pd.DataFrame(index=metrics)

    # Fill columns for each algo+resource we actually have
    for (algo, resource), path in sorted(algo_paths.items(), key=lambda x: (ALGORITHMS.index(x[0][0]), x[0][1])):
        algo_hot = normalize_algo(path)
        mdf = per_window_metrics(oracle, algo_hot)

        col = f"{algo}.{resource}"

        if mdf.empty:
            report.loc["num_windows", col] = 0
            report.loc["avg_k", col] = 0.0
            report.loc["avg_recall@k", col] = "0.000000"
            report.loc["avg_access_count_ratio", col] = "0.000000"
            continue

        report.loc["num_windows", col] = int(mdf["window"].nunique())
        report.loc["avg_k", col] = float(mdf["k"].mean())
        report.loc["avg_recall@k", col] = float(mdf["recall@k"].mean())
        report.loc["avg_access_count_ratio", col] = float(mdf["access_count_ratio"].mean())

    # Sort columns as requested: algo order, then resource size ascending
    report = report[sorted(report.columns, key=col_sort_key)]
    report.index.name = ""

    out_path = root / f"{prefix}.{epoch}.report.csv"
    report.to_csv(out_path, index=True, header=True)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="Folder containing <prefix>.<epoch>.*.*.csv")
    ap.add_argument("--prefix", required=True, help="Exact <prefix> to match (before .<epoch>...)")  # NEW [web:62]
    args = ap.parse_args()

    root = Path(args.dir)
    if not root.exists() or not root.is_dir():
        raise RuntimeError(f"--dir is not a directory: {root}")

    out_path = build_report(root, args.prefix)  # CHANGED
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
