import mmh3
from .base import BaseTracker


class CMSketch(BaseTracker):
    def __init__(self, width, depth, k, **kwargs):
        super().__init__(**kwargs)
        self.name = f"CMSketch(w={width}, d={depth}, k={k})"

        self.width = width
        self.depth = depth
        self.k = k
        self.size = width * depth
        self.table = [[0] * width for _ in range(depth)]
        self.seeds = list(range(depth))

        # key: item/address, value: estimated count (from CM sketch)
        self.hot_items = {}

    def _hash(self, item, seed):
        if isinstance(item, str) and item.startswith("0x"):
            val = int(item, 16)
            key = val.to_bytes((val.bit_length() + 7) // 8, "big")
            return mmh3.hash(key, seed) % self.width
        return mmh3.hash(str(item), seed) % self.width

    def _estimate(self, item):
        # CM estimate = min over rows [web:58]
        est = float("inf")
        for i in range(self.depth):
            idx = self._hash(item, self.seeds[i])
            c = self.table[i][idx]
            if c < est:
                est = c
        return 0 if est == float("inf") else est

    def update(self, item):
        # 1) Update sketch counters
        for i in range(self.depth):
            idx = self._hash(item, self.seeds[i])
            self.table[i][idx] += 1

        # 2) Get estimated count after update
        est = self._estimate(item)  # min across rows [web:58]

        # 3) Maintain hot_items of size k using replace-min policy [web:55]
        if item in self.hot_items:
            self.hot_items[item] = est
            return

        if len(self.hot_items) < self.k:
            self.hot_items[item] = est
            return

        # hot_items full -> compare with current min in hot_items
        min_item = min(self.hot_items, key=self.hot_items.get)
        min_val = self.hot_items[min_item]

        if est > min_val:
            del self.hot_items[min_item]
            self.hot_items[item] = est
        # else: drop

    def query(self):
        # Return current candidate top-k (sorted)
        return sorted(self.hot_items.items(), key=lambda x: x[1], reverse=True)

    def reset(self):
        self.table = [[0] * self.width for _ in range(self.depth)]
        self.hot_items.clear()
