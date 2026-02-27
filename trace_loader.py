'''''
def load_trace(file_path):
    """
    Generator that yields physical addresses from the trace file.
    Assumes format: "timestamp (picosecond) Address" (e.g., "1325103 0x12a04f")
    """
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.split()
            cycle = int(parts[0])
            addr = int(parts[1], 16)
            yield cycle, addr
'''

import re

def load_trace(file_path):
    """
    Expected line format: "<timestamp_ps> <hex_addr>"
    Example: "1325103 0x12a04f"
    """
    with open(file_path, "r", errors="ignore") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 2:
                continue

            try:
                ts = int(parts[0])
                full_addr = int(parts[1], 16)
            except ValueError:
                continue

            page_addr = full_addr >> 12
            yield ts, page_addr
