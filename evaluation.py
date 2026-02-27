import argparse
import csv
import os

from trace_loader import load_trace

from algorithms.oracle import Oracle
from algorithms.cm_sketch import CMSketch
from algorithms.space_saving import SpaceSaving
from algorithms.sticky_sampling import StickySampling
from algorithms.lossy_counting import LossyCounting
from algorithms.set_associative import SetAssociativeLFU
from algorithms.set_associative import SetAssociativeLRU
from algorithms.set_associative import SetAssociativeDROP
from algorithms.counter_trie import CounterTrie

PS_PER_MS = 1_000_000_000  # 1ms = 1e9 ps

def trace_prefix(trace_path: str) -> str:
    base = os.path.basename(trace_path)
    base, _ = os.path.splitext(base)   
    base, _ = os.path.splitext(base)
    return base

def run_one(trace_path, tracker, query_interval_ps, out_csv_path):
    loader = load_trace(trace_path)

    first = True
    next_query_ts = None
    window_idx = 0

    with open(out_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["window_idx", "item", "est_count"])

        for record in loader:
            if not isinstance(record, tuple) or len(record) < 2:
                raise ValueError("Expected tuple record like (timestamp_ps, address, ...)")

            ts = int(record[0])
            addr = record[1]

            if first:
                next_query_ts = ts + query_interval_ps
                first = False

            tracker.update(addr)

            while ts >= next_query_ts:
                hot = tracker.query()
                print(f"[{tracker.name}] window={window_idx} ts={int(next_query_ts/PS_PER_MS)} ms hot={len(hot)}")

                for item, est_count in hot:
                    writer.writerow([window_idx, hex(int(item)), int(est_count)])

                tracker.reset()
                window_idx += 1
                next_query_ts += query_interval_ps
                
        if not first:
            hot = tracker.query()
            print(f"[{tracker.name}] window={window_idx} ts=end hot={len(hot)} (final flush)")
            for item, est_count in hot:
                writer.writerow([window_idx, hex(int(item)), int(est_count)])

def build_trackers():

    trackers = []
    trackers.append(Oracle())

    trackers.append(CMSketch(width=128 * 1024, depth=4, k=500))
    trackers.append(CMSketch(width=64 * 1024, depth=4, k=500))
    trackers.append(CMSketch(width=32 * 1024, depth=4, k=500))
    trackers.append(CMSketch(width=16 * 1024, depth=4, k=500))
    trackers.append(CMSketch(width=8 * 1024, depth=4, k=500))
    trackers.append(CMSketch(width=4 * 1024, depth=4, k=500))

    trackers.append(SpaceSaving(n=1024, k=500))
    trackers.append(SpaceSaving(n=512, k=500))
    trackers.append(SpaceSaving(n=256, k=256))
    trackers.append(SpaceSaving(n=128, k=128))

    #trackers.append(SetAssociativeLFU(num_sets=32*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeLFU(num_sets=16*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeLFU(num_sets=8*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeLFU(num_sets=4*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeLFU(num_sets=2*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeLFU(num_sets=1024, ways=4, counter_bits=16, k=500))

    #trackers.append(SetAssociativeLRU(num_sets=32*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeLRU(num_sets=16*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeLRU(num_sets=8*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeLRU(num_sets=4*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeLRU(num_sets=2*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeLRU(num_sets=1024, ways=4, counter_bits=16, k=500))

    #trackers.append(SetAssociativeDROP(num_sets=32*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeDROP(num_sets=16*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeDROP(num_sets=8*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeDROP(num_sets=4*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeDROP(num_sets=2*1024, ways=4, counter_bits=16, k=500))
    #trackers.append(SetAssociativeDROP(num_sets=1024, ways=4, counter_bits=16, k=500))

    trackers.append(StickySampling(s=0.003, epsilon=1e-3, delta=1e-3, k=500, max_entries=8192))
    #trackers.append(StickySampling(s=0.003, epsilon=1e-3, delta=1e-3, k=500, max_entries=4096))
    #trackers.append(StickySampling(s=0.003, epsilon=1e-3, delta=1e-3, k=500, max_entries=2048))
    #trackers.append(StickySampling(s=0.003, epsilon=1e-3, delta=1e-3, k=500, max_entries=1024))
    #trackers.append(StickySampling(s=0.003, epsilon=1e-3, delta=1e-3, k=500, max_entries=512))
    #trackers.append(StickySampling(s=0.003, epsilon=1e-3, delta=1e-3, k=256, max_entries=256))

    trackers.append(LossyCounting(s=0.003, epsilon=1e-3, k=500, max_entries=8192))
    #trackers.append(LossyCounting(s=0.003, epsilon=1e-3, k=500, max_entries=4096))
    #trackers.append(LossyCounting(s=0.003, epsilon=1e-3, k=500, max_entries=2048))
    #trackers.append(LossyCounting(s=0.003, epsilon=1e-3, k=500, max_entries=1024))
    #trackers.append(LossyCounting(s=0.003, epsilon=1e-3, k=500, max_entries=512))
    #trackers.append(LossyCounting(s=0.003, epsilon=1e-3, k=256, max_entries=256))

    #trackers.append(CounterTrie(addr_space_bytes=64*1024**3, base_region_bytes=1*1024**3, page_bytes=4*1024, max_nodes=128*1024, per_level_threshold=5, last_level_threshold=1, k=500))
    #trackers.append(CounterTrie(addr_space_bytes=64*1024**3, base_region_bytes=1*1024**3, page_bytes=4*1024, max_nodes=64*1024, per_level_threshold=5, last_level_threshold=1, k=500))
    #trackers.append(CounterTrie(addr_space_bytes=64*1024**3, base_region_bytes=1*1024**3, page_bytes=4*1024, max_nodes=32*1024, per_level_threshold=5, last_level_threshold=1, k=500))
    #trackers.append(CounterTrie(addr_space_bytes=64*1024**3, base_region_bytes=1*1024**3, page_bytes=4*1024, max_nodes=16*1024, per_level_threshold=5, last_level_threshold=1, k=500))
    
    return trackers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True, help="Input trace file path")
    parser.add_argument("--query-ms", type=int, default=1, help="Query interval in ms")
    parser.add_argument("--out-dir", default=".", help="Directory to write <prefix>.<algo>.csv")
    args = parser.parse_args()

    prefix = trace_prefix(args.trace)
    query_interval_ps = args.query_ms * PS_PER_MS

    out_dir = args.out_dir + f"/{args.query_ms}ms/{prefix}"
    os.makedirs(out_dir, exist_ok=True)

    for tracker in build_trackers():
        algo_tag = tracker.__class__.__name__.lower()

        if (int(tracker.size) >= 1024):
            size = f".{tracker.size//1024}k"
        else:
            size = f".{tracker.size}"

        out_csv = os.path.join(out_dir, f"{prefix}.{args.query_ms}ms.{algo_tag}.{tracker.size}.csv")

        print(f"== Running {tracker.name} -> {out_csv}")
        run_one(args.trace, tracker, query_interval_ps, out_csv)


if __name__ == "__main__":
    main()
