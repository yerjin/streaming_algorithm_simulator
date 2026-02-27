import pickle
import argparse
import csv
from collections import Counter
from trace_loader import load_trace

def generate_ground_truth(trace_path, output_path):

    print(f"[PAC] Processing trace: {trace_path} ...")
    
    counter = Counter()
    total_items = 0
    
    loader = load_trace(trace_path)
    for record in loader:
        if isinstance(record, tuple):
            addr = record[1]
        else:
            addr = record
            
        counter[addr] += 1
        total_items += 1
        
        if total_items % 10000000 == 0:
            print(f"Processed {int(total_items / 1000000)} M items...")

    print(f"[PAC] Total items processed: {total_items}")
    print(f"[PAC] Unique items found: {len(counter)}")

    result_data = dict(counter)

    final_output = {
        "total_count": total_items,
        "counts": result_data,
        "trace_file": trace_path
    }

    print(f"[PAC] Sorting data by count (descending)...")

    sorted_items = sorted(result_data.items(), key=lambda item: item[1], reverse=True)

    # ================= Statistics =================
    total_sum = total_items
    top_100_items = sorted_items[:100]
    top_100_sum = sum(count for addr, count in top_100_items)
    top_100_ratio = (top_100_sum / total_sum) * 100 if total_sum > 0 else 0 

    top_1000_items = sorted_items[:1000]
    top_1000_sum = sum(count for addr, count in top_1000_items)
    top_1000_ratio = (top_1000_sum / total_sum) * 100 if total_sum > 0 else 0 

    top_10000_items = sorted_items[:10000]
    top_10000_sum = sum(count for addr, count in top_10000_items)
    top_10000_ratio = (top_10000_sum / total_sum) * 100 if total_sum > 0 else 0 
    

    print("-" * 40)
    print(f"[Statistics]")
    print(f"Total Count:   {total_sum:,}")
    print(f"Top-100 Count Sum: {top_100_sum:,}")
    print(f"Top-100 Ratio:     {top_100_ratio:.2f}%")
    print(f"Top-1000 Count Sum: {top_1000_sum:,}")
    print(f"Top-1000 Ratio:     {top_1000_ratio:.2f}%")
    print(f"Top-10000 Count Sum: {top_10000_sum:,}")
    print(f"Top-10000 Ratio:     {top_10000_ratio:.2f}%")


    print("-" * 40)
    # ==========================================================

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Address_Hex", "Count"])
        sorted_data = sorted(result_data.items(), key=lambda item: item[1], reverse=True)

    with open(output_path, 'w') as f:
        for addr, count in sorted_data:
            f.write(f"{hex(addr)},{count}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True, help="Input trace file path")
    parser.add_argument("--output", default="ground_truth.csv", help="Output pickle file path")
    
    args = parser.parse_args()
    
    generate_ground_truth(args.trace, args.output)
