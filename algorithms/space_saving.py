from .base import BaseTracker


class SpaceSaving(BaseTracker):
    def __init__(self, n, k, **kwargs):
        super().__init__(**kwargs)
        self.name = f"SpaceSaving(n={n}, k={k})"
        self.size = n
        self.n = n  # table size (number of counters)
        self.k = k  # number of items to return on query
        self.counts = {}

    def update(self, address):
        if address in self.counts:
            self.counts[address] += 1
        else:
            if len(self.counts) < self.n:
                self.counts[address] = 1
            else:
                min_addr = min(self.counts, key=self.counts.get)
                min_val = self.counts[min_addr]
                del self.counts[min_addr]
                self.counts[address] = min_val + 1  # Space-Saving replace-min rule

    # --- Optional decay (disabled by default) ---
    def _decay_by_min(self):
        """
        Optional: subtract the current minimum counter from all counters
        and drop non-positive entries.
        NOTE: This mutates state; keep disabled unless you intentionally want aging/windowing behavior.
        """
        if not self.counts:
            return

        min_val = min(self.counts.values())
        if min_val <= 0:
            return

        decay_remove = []
        for addr in list(self.counts.keys()):
            self.counts[addr] -= min_val
            if self.counts[addr] <= 0:
                decay_remove.append(addr)

        for addr in decay_remove:
            del self.counts[addr]

    def query(self):
        # 1) Return top-k
        kk = min(self.k, len(self.counts))
        topk = sorted(self.counts.items(), key=lambda x: x[1], reverse=True)[:kk]

        # 2) Optional decay on query
        # self._decay_by_min()

        return topk

    def reset(self):
        self.counts.clear()
