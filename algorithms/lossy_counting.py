import math
from .base import BaseTracker


class LossyCounting(BaseTracker):
    def __init__(self, s, epsilon, k, max_entries=None, **kwargs):
        super().__init__(**kwargs)
        self.name = f"LossyCounting(s={s}, e={epsilon}, k={k})"

        self.s = s
        self.e = epsilon
        self.k = int(k)
    
        self.w = int(math.ceil(1.0 / epsilon))
        self.total_processed = 0

        self.max_entries = None if max_entries is None else max(1, int(max_entries))
        self.counts = {}  # addr -> [f, delta]

        self.size = self.max_entries

    def _bucket_id(self):
        return int(math.ceil(self.total_processed / self.w)) if self.total_processed > 0 else 1

    def update(self, address):
        self.total_processed += 1
        b = self._bucket_id()

        if address in self.counts:
            self.counts[address][0] += 1
        else:
            if self.max_entries is None or len(self.counts) < self.max_entries:
                self.counts[address] = [1, b - 1]
            else:
                pass

        # prune at bucket boundaries: whenever N mod w == 0
        if (self.total_processed % self.w) == 0:
            self._prune()

    def _prune(self):
        b = self._bucket_id()
        to_delete = []
        for e, (f, delta) in self.counts.items():
            # drop if f + delta <= bucket_id
            if (f + delta) <= b:
                to_delete.append(e)
        for e in to_delete:
            del self.counts[e]

    def query(self):
        kk = min(self.k, len(self.counts))
        res = sorted(((addr, fd[0]) for addr, fd in self.counts.items()),
                     key=lambda x: x[1], reverse=True)[:kk]
        return res

    def reset(self):
        self.counts.clear()
        self.total_processed = 0
