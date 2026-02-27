#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd


# 사용자가 원하는 행(=prefix) 정렬 순서
ORDER = [
    "607.cactuBSSN_s-2421B",
    "607.cactuBSSN_s-3477B",
    "607.cactuBSSN_s-4004B",
    "607.cactuBSSN_s-4248B",
    "649.fotonik3d_s-10881B",
    "649.fotonik3d_s-1176B",
    "649.fotonik3d_s-1B",
    "649.fotonik3d_s-7084B",
    "649.fotonik3d_s-8225B",
    "654.roms_s-1007B",
    "654.roms_s-1021B",
    "654.roms_s-1070B",
    "654.roms_s-1390B",
    "654.roms_s-1613B",
    "654.roms_s-293B",
    "654.roms_s-294B",
    "654.roms_s-523B",
    "654.roms_s-842B",
    "429.mcf-184B",
    "429.mcf-192B",
    "429.mcf-217B",
    "429.mcf-22B",
    "429.mcf-51B",
    "redis.000",
    "redis.001",
    "redis.002",
    "redis.003",
    "redis.004",
    "redis.005",
    "redis.006",
    "redis.007",
    "redis.008",
    "redis.009",
    "pagerank.000",
]
order_rank = {p: i for i, p in enumerate(ORDER)}


def sort_prefix_index(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    wanted = [p for p in ORDER if p in df.index]
    extra = [p for p in df.index if p not in order_rank]
    return df.reindex(wanted + sorted(extra))  # reindex로 순서 강제 [web:147]


def collect_metric(results_epoch_dir: Path, metric_row: str, suffix: str) -> pd.DataFrame:
    """
    results_epoch_dir: ./results/<epoch>/
    suffix: ".report.csv" or ".pacreport.csv"
    metric_row: "avg_access_count_ratio" or "coverage_ratio"
    Returns: DataFrame with rows=prefix, cols=algo(/algo.resource...)
    """
    rows = []

    # ./results/<epoch>/<prefix>/ 순회
    for prefix_dir in sorted(results_epoch_dir.iterdir()):
        if not prefix_dir.is_dir():
            continue

        prefix = prefix_dir.name
        csv_path = prefix_dir / f"{prefix}.{results_epoch_dir.name}{suffix}"
        if not csv_path.exists():
            continue

        df = pd.read_csv(csv_path, index_col=0)  # 첫 컬럼을 index로 [web:9]
        if metric_row not in df.index:
            raise RuntimeError(f"{csv_path}: '{metric_row}' row not found. Rows={list(df.index)[:10]}...")

        s = df.loc[metric_row]
        s.name = prefix
        rows.append(s)

    if not rows:
        raise RuntimeError(f"No '{suffix}' CSVs found under {results_epoch_dir}")

    out = pd.DataFrame(rows)
    out.index.name = "prefix"
    return sort_prefix_index(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="./results", help="Base results dir (default: ./results)")
    ap.add_argument("--epoch", required=True, help="Epoch length directory name, e.g., 1ms")
    args = ap.parse_args()

    base = Path(args.results)
    epoch_dir = base / args.epoch
    if not epoch_dir.exists() or not epoch_dir.is_dir():
        raise RuntimeError(f"Epoch dir not found: {epoch_dir}")

    # 1) <epoch>.report.csv  (avg_access_count_ratio)
    df_report = collect_metric(epoch_dir, metric_row="avg_access_count_ratio", suffix=".report.csv")
    out_report = Path(f"{args.epoch}.report.csv")
    df_report.to_csv(out_report, index=True, header=True)
    print(f"Wrote {out_report} ({df_report.shape[0]} rows, {df_report.shape[1]} cols)")

    # 2) <epoch>.pacreport.csv (coverage_ratio)
    df_pac = collect_metric(epoch_dir, metric_row="coverage_ratio", suffix=".pacreport.csv")
    out_pac = Path(f"{args.epoch}.pacreport.csv")
    df_pac.to_csv(out_pac, index=True, header=True)
    print(f"Wrote {out_pac} ({df_pac.shape[0]} rows, {df_pac.shape[1]} cols)")


if __name__ == "__main__":
    main()
