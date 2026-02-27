#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd


ALGORITHMS = [
    "oracle",
    "cmsketch",
    "spacesaving",
    "stickysampling",
    "lossycounting",
    "setassociativelfu",
    "setassociativelru",
    "setassociativedrop",
    "countertrie",
]


def load_pac(pac_csv_path: Path):
    df = pd.read_csv(pac_csv_path, header=None, names=["item", "true_count"])
    df["item"] = df["item"].astype(str).str.strip()
    df["true_count"] = df["true_count"].astype(int)
    df = df.groupby("item", as_index=False)["true_count"].sum()
    df_sorted = df.sort_values("true_count", ascending=False).reset_index(drop=True)
    true_map = dict(zip(df_sorted["item"], df_sorted["true_count"]))
    return df_sorted, true_map


def load_algo_unique_items(algo_csv_path: Path, algo_name: str, oracle_topn: int = 5):
    df = pd.read_csv(algo_csv_path)

    if "item" not in df.columns:
        raise RuntimeError(f"Missing 'item' column in {algo_csv_path}")
    df["item"] = df["item"].astype(str).str.strip()

    if algo_name == "oracle":
        for col in ["window_idx", "est_count"]:
            if col not in df.columns:
                raise RuntimeError(f"Missing '{col}' column in {algo_csv_path} (oracle mode)")

        df["window_idx"] = df["window_idx"].astype(int)
        df["est_count"] = df["est_count"].astype(int)

        topn_df = (
            df.sort_values(["window_idx", "est_count"], ascending=[True, False])
              .groupby("window_idx", as_index=False, sort=False)
              .head(oracle_topn)
        )

        topn_df = topn_df.drop_duplicates(subset=["item"], keep="first")
        return set(topn_df["item"].tolist())

    return set(df["item"].tolist())


def compute_metrics_for_algo(pac_df, true_map, algo_items):
    K = len(algo_items)
    if K == 0:
        return {
            "k": 0,
            "algo_true_sum_over_k": 0,
            "pac_true_topk_sum": 0,
            "coverage_ratio": 0.0,
            "recall@k": 0.0,
        }

    algo_true_sum = int(sum(true_map.get(item, 0) for item in algo_items))
    pac_topk_sum = int(pac_df.head(K)["true_count"].sum())
    ratio = (algo_true_sum / pac_topk_sum) if pac_topk_sum > 0 else 0.0

    pac_topk_set = set(pac_df.head(K)["item"].tolist())
    hit = len(pac_topk_set.intersection(algo_items))
    recall_at_k = hit / K if K > 0 else 0.0

    return {
        "k": K,
        "algo_true_sum_over_k": algo_true_sum,
        "pac_true_topk_sum": pac_topk_sum,
        "coverage_ratio": ratio,
        "recall@k": recall_at_k,
    }


def parse_algo_filename(p: Path):
    # <prefix>.<epoch>.<algo>.<resource>.csv
    # prefix contains dots -> parse from the end
    name = p.name
    if not name.endswith(".csv"):
        return None
    stem = name[:-4]
    parts = stem.split(".")
    if len(parts) < 4:
        return None

    resource_str = parts[-1]
    if not resource_str.isdigit():  # skip *.report.csv 같은 것들
        return None

    resource = int(resource_str)
    algo = parts[-2]
    epoch = parts[-3]
    prefix = ".".join(parts[:-3])
    return prefix, epoch, algo, resource


def col_sort_key(col: str):
    # col like "cmsketch.16384"
    algo, res = col.rsplit(".", 1)
    algo_idx = ALGORITHMS.index(algo) if algo in ALGORITHMS else 10**9
    return (algo_idx, int(res))


def discover_epoch_and_paths(root: Path, prefix: str):
    """
    - pac: <prefix>.pac.csv  (epoch 없음)
    - oracle/algo: <prefix>.<epoch>.<algo>.<resource>.csv
      (oracle는 resource=0 하나만 있다고 가정)
    Returns: epoch, oracle_path, algo_paths[(algo,resource)]=Path
    """
    oracle_path = None
    algo_paths = {}
    epochs = set()

    for p in root.glob("*.csv"):
        parsed = parse_algo_filename(p)
        if not parsed:
            continue
        pfx, epoch, algo, resource = parsed
        if pfx != prefix:
            continue

        epochs.add(epoch)

        if algo == "oracle":
            if resource != 0:
                raise RuntimeError(f"Oracle resource must be 0, got {p}")
            if oracle_path is not None and oracle_path != p:
                raise RuntimeError(f"Multiple oracle files found: {oracle_path}, {p}")
            oracle_path = p
        else:
            algo_paths[(algo, resource)] = p

    if len(epochs) != 1:
        raise RuntimeError(f"Expected exactly one epoch for prefix={prefix}, found: {sorted(epochs)}")
    epoch = next(iter(epochs))

    if oracle_path is None:
        raise RuntimeError(f"Oracle file not found for prefix={prefix} in {root}")

    return epoch, oracle_path, algo_paths


def build_report(root: Path, prefix: str):
    pac_path = root / f"{prefix}.pac.csv"
    if not pac_path.exists():
        raise RuntimeError(f"pac file not found: {pac_path}")

    pac_df, true_map = load_pac(pac_path)
    pac_total_addrs = int(len(pac_df))

    epoch, oracle_path, algo_paths = discover_epoch_and_paths(root, prefix)

    # rows(=metric) x cols(=algo.resource)
    metrics = ["pac_total_addrs", "k", "algo_true_sum_over_k", "pac_true_topk_sum", "coverage_ratio", "recall@k"]
    report = pd.DataFrame(index=metrics)

    # oracle column: "oracle.0"
    oracle_items = load_algo_unique_items(oracle_path, algo_name="oracle", oracle_topn=5)
    m = compute_metrics_for_algo(pac_df, true_map, oracle_items)
    report.loc["pac_total_addrs", "oracle.0"] = pac_total_addrs
    report.loc["k", "oracle.0"] = m["k"]
    report.loc["algo_true_sum_over_k", "oracle.0"] = m["algo_true_sum_over_k"]
    report.loc["pac_true_topk_sum", "oracle.0"] = m["pac_true_topk_sum"]
    report.loc["coverage_ratio", "oracle.0"] = float(m["coverage_ratio"])
    report.loc["recall@k", "oracle.0"] = float(m["recall@k"])

    # other algos/resources
    for (algo, resource), path in algo_paths.items():
        if algo not in ALGORITHMS:
            continue
        algo_items = load_algo_unique_items(path, algo_name=algo, oracle_topn=5)
        m = compute_metrics_for_algo(pac_df, true_map, algo_items)
        col = f"{algo}.{resource}"

        report.loc["pac_total_addrs", col] = pac_total_addrs
        report.loc["k", col] = m["k"]
        report.loc["algo_true_sum_over_k", col] = m["algo_true_sum_over_k"]
        report.loc["pac_true_topk_sum", col] = m["pac_true_topk_sum"]
        report.loc["coverage_ratio", col] = float(m["coverage_ratio"])
        report.loc["recall@k", col] = float(m["recall@k"])

    # sort columns by algo order, then resource asc
    report = report[sorted(report.columns, key=col_sort_key)]
    report.index.name = ""

    # 저장 직전에만 6자리 포맷(문자열)
    out_path = root / f"{prefix}.{epoch}.pacreport.csv"
    report.to_csv(out_path, index=True, header=True, float_format="%.6f")

    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="Folder containing <prefix>.pac.csv and <prefix>.<epoch>.*.*.csv")
    ap.add_argument("--prefix", required=True, help="Example: 607.cactuBSSN_s-2421B")
    args = ap.parse_args()

    root = Path(args.dir)
    if not root.exists() or not root.is_dir():
        raise RuntimeError(f"--dir is not a directory: {root}")

    out_path = build_report(root, args.prefix)
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
