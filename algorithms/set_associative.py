import math
from .base import BaseTracker


class SetAssociativeLFU(BaseTracker):
    def __init__(
        self,
        num_sets: int = 16 * 1024,
        num_ways: int = 4,
        counter_bits: int = 12,
        k: int = 1024,                 # NEW: size of hot list
        use_python_hash: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        assert num_sets > 0
        assert num_ways > 0
        assert counter_bits > 0
        assert k >= 0

        self.name = f"SetAssociativeLFU(sets={num_sets}, ways={num_ways}, cbits={counter_bits}, k={k})"

        self.num_sets = int(num_sets)
        self.num_ways = int(num_ways)
        self.counter_bits = int(counter_bits)
        self.counter_max = (1 << self.counter_bits) - 1
        self.k = int(k)
        self.use_python_hash = bool(use_python_hash)
        self.size = self.num_sets * self.num_ways

        # hot items: key=address, val=count
        self.hot_items = {}

        # Per-set storage
        self.valid = [[False] * self.num_ways for _ in range(self.num_sets)]
        self.tags  = [[None]  * self.num_ways for _ in range(self.num_sets)]
        self.cnt   = [[0]     * self.num_ways for _ in range(self.num_sets)]

        # Per-set tie-break pointer (round-robin start)
        self.rr_ptr = [0] * self.num_sets

        self.total_processed = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _idx(self, address: int) -> int:
        if self.use_python_hash:
            h = hash(address)
        else:
            x = int(address) & ((1 << 64) - 1)
            x ^= (x >> 33)
            x *= 0xff51afd7ed558ccd
            x &= ((1 << 64) - 1)
            x ^= (x >> 33)
            h = x
        return h % self.num_sets

    def _sat_inc(self, v: int) -> int:
        return v + 1 if v < self.counter_max else self.counter_max

    def _hot_try_update(self, address: int, est_cnt: int):
        """Maintain a top-k dictionary by replacing the current minimum when beneficial."""
        if self.k == 0:
            return

        if address in self.hot_items:
            # refresh stored count (monotonic non-decreasing here)
            if est_cnt > self.hot_items[address]:
                self.hot_items[address] = est_cnt
            return

        if len(self.hot_items) < self.k:
            self.hot_items[address] = est_cnt
            return

        # full -> replace current min if new is larger
        min_addr = min(self.hot_items, key=self.hot_items.get)
        min_val = self.hot_items[min_addr]
        if est_cnt > min_val:
            del self.hot_items[min_addr]
            self.hot_items[address] = est_cnt
        # else drop

    def update(self, address: int):
        self.total_processed += 1
        s = self._idx(address)

        # Tag compare in set
        hit_way = -1
        for w in range(self.num_ways):
            if self.valid[s][w] and self.tags[s][w] == address:
                hit_way = w
                break

        if hit_way >= 0:
            self.hits += 1
            new_cnt = self._sat_inc(self.cnt[s][hit_way])
            self.cnt[s][hit_way] = new_cnt

            # NEW: always try to feed top-k with (address, count)
            self._hot_try_update(address, new_cnt)
            return

        # miss: allocate/evict within set
        self.misses += 1

        start = self.rr_ptr[s]
        free_way = -1
        for off in range(self.num_ways):
            w = (start + off) % self.num_ways
            if not self.valid[s][w]:
                free_way = w
                break

        if free_way >= 0:
            victim = free_way
        else:
            min_cnt = None
            victim = None
            for off in range(self.num_ways):
                w = (start + off) % self.num_ways
                c = self.cnt[s][w]
                if (min_cnt is None) or (c < min_cnt):
                    min_cnt = c
                    victim = w
            self.evictions += 1

        # allocate into victim
        self.valid[s][victim] = True
        self.tags[s][victim] = address
        self.cnt[s][victim] = 1

        # NEW: also feed hot list on insertion (count=1)
        self._hot_try_update(address, 1)

        # rr_ptr 갱신
        self.rr_ptr[s] = (victim + 1) % self.num_ways

    def query(self):
        # Return current hot_items (size <= k) sorted by count desc
        return sorted(self.hot_items.items(), key=lambda x: x[1], reverse=True)

    def reset(self):
        for s in range(self.num_sets):
            for w in range(self.num_ways):
                self.valid[s][w] = False
                self.tags[s][w] = None
                self.cnt[s][w] = 0
            self.rr_ptr[s] = 0

        self.hot_items.clear()
        self.total_processed = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0

class SetAssociativeLRU(BaseTracker):
    def __init__(
        self,
        num_sets: int = 16 * 1024,
        num_ways: int = 4,
        counter_bits: int = 12,          # LFU와 인터페이스 맞추기용(미사용)
        k: int = 1024,                   # LFU와 동일: hot list size
        use_python_hash: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        assert num_sets > 0
        assert num_ways > 0
        assert counter_bits > 0
        assert k >= 0
        assert (num_ways & (num_ways - 1)) == 0, "tree-PLRU needs power-of-two ways"

        self.name = f"SetAssociativeLRU(sets={num_sets}, ways={num_ways}, cbits={counter_bits}, k={k})"

        self.num_sets = int(num_sets)
        self.num_ways = int(num_ways)
        self.counter_bits = int(counter_bits)
        self.counter_max = (1 << self.counter_bits) - 1
        self.k = int(k)
        self.use_python_hash = bool(use_python_hash)
        self.size = self.num_sets * self.num_ways

        # hot items: key=address, val=count(여기선 recency 기반 정책이라 카운트는 "참고용"으로만 사용)
        self.hot_items = {}

        # Per-set storage (LFU와 동일)
        self.valid = [[False] * self.num_ways for _ in range(self.num_sets)]
        self.tags  = [[None]  * self.num_ways for _ in range(self.num_sets)]

        # LFU에 있던 cnt 배열도 “형태 일치”를 위해 유지 (LRU에서는 안 써도 됨)
        self.cnt   = [[0] * self.num_ways for _ in range(self.num_sets)]

        # tree-PLRU bits: ways-1 per set
        self.plru = [[0] * (self.num_ways - 1) for _ in range(self.num_sets)]

        # LFU와 동일 필드 유지
        self.rr_ptr = [0] * self.num_sets

        self.total_processed = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _idx(self, address: int) -> int:
        if self.use_python_hash:
            h = hash(address)
        else:
            x = int(address) & ((1 << 64) - 1)
            x ^= (x >> 33)
            x *= 0xff51afd7ed558ccd
            x &= ((1 << 64) - 1)
            x ^= (x >> 33)
            h = x
        return h % self.num_sets

    def _sat_inc(self, v: int) -> int:
        return v + 1 if v < self.counter_max else self.counter_max

    def _hot_try_update(self, address: int, est_cnt: int):
        if self.k == 0:
            return

        if address in self.hot_items:
            if est_cnt > self.hot_items[address]:
                self.hot_items[address] = est_cnt
            return

        if len(self.hot_items) < self.k:
            self.hot_items[address] = est_cnt
            return

        min_addr = min(self.hot_items, key=self.hot_items.get)
        min_val = self.hot_items[min_addr]
        if est_cnt > min_val:
            del self.hot_items[min_addr]
            self.hot_items[address] = est_cnt

    def _plru_access(self, s: int, way: int):
        idx = 0
        lo, hi = 0, self.num_ways
        while (hi - lo) > 1:
            mid = (lo + hi) // 2
            if way < mid:
                self.plru[s][idx] = 1  # next victim from RIGHT
                idx = 2 * idx + 1
                hi = mid
            else:
                self.plru[s][idx] = 0  # next victim from LEFT
                idx = 2 * idx + 2
                lo = mid

    def _plru_victim(self, s: int) -> int:
        idx = 0
        lo, hi = 0, self.num_ways
        while (hi - lo) > 1:
            mid = (lo + hi) // 2
            b = self.plru[s][idx]
            if b == 0:
                idx = 2 * idx + 1
                hi = mid
            else:
                idx = 2 * idx + 2
                lo = mid
        return lo

    def update(self, address: int):
        self.total_processed += 1
        s = self._idx(address)

        # Tag compare in set
        hit_way = -1
        for w in range(self.num_ways):
            if self.valid[s][w] and self.tags[s][w] == address:
                hit_way = w
                break

        if hit_way >= 0:
            self.hits += 1

            # LFU처럼 cnt도 올려서 hot list에 넣고 싶으면 이렇게(“인터페이스/동작 유사화”)
            new_cnt = self._sat_inc(self.cnt[s][hit_way])
            self.cnt[s][hit_way] = new_cnt
            self._hot_try_update(address, new_cnt)

            # LRU 핵심: recency 갱신
            self._plru_access(s, hit_way)
            return

        # miss
        self.misses += 1

        # free way first (LFU와 동일)
        start = self.rr_ptr[s]
        free_way = -1
        for off in range(self.num_ways):
            w = (start + off) % self.num_ways
            if not self.valid[s][w]:
                free_way = w
                break

        if free_way >= 0:
            victim = free_way
        else:
            victim = self._plru_victim(s)
            self.evictions += 1

        # allocate
        self.valid[s][victim] = True
        self.tags[s][victim] = address
        self.cnt[s][victim] = 1

        self._hot_try_update(address, 1)
        self._plru_access(s, victim)

        # rr_ptr 갱신 (형태 유지용; LRU 자체엔 필수는 아님)
        self.rr_ptr[s] = (victim + 1) % self.num_ways

    def query(self):
        return sorted(self.hot_items.items(), key=lambda x: x[1], reverse=True)

    def reset(self):
        for s in range(self.num_sets):
            for w in range(self.num_ways):
                self.valid[s][w] = False
                self.tags[s][w] = None
                self.cnt[s][w] = 0
            self.rr_ptr[s] = 0
            for i in range(self.num_ways - 1):
                self.plru[s][i] = 0

        self.hot_items.clear()
        self.total_processed = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0

class SetAssociativeDROP(BaseTracker):
    def __init__(
        self,
        num_sets: int = 16 * 1024,
        num_ways: int = 4,
        counter_bits: int = 12,
        k: int = 1024,
        use_python_hash: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        assert num_sets > 0
        assert num_ways > 0
        assert counter_bits > 0
        assert k >= 0

        self.name = f"SetAssociativeDROP(sets={num_sets}, ways={num_ways}, cbits={counter_bits}, k={k})"

        self.num_sets = int(num_sets)
        self.num_ways = int(num_ways)
        self.counter_bits = int(counter_bits)
        self.counter_max = (1 << self.counter_bits) - 1
        self.k = int(k)
        self.use_python_hash = bool(use_python_hash)
        self.size = self.num_sets * self.num_ways

        self.hot_items = {}

        self.valid = [[False] * self.num_ways for _ in range(self.num_sets)]
        self.tags  = [[None]  * self.num_ways for _ in range(self.num_sets)]
        self.cnt   = [[0]     * self.num_ways for _ in range(self.num_sets)]
        self.rr_ptr = [0] * self.num_sets

        self.total_processed = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0  # DROP에서는 증가 안 함

    def _idx(self, address: int) -> int:
        if self.use_python_hash:
            h = hash(address)
        else:
            x = int(address) & ((1 << 64) - 1)
            x ^= (x >> 33)
            x *= 0xff51afd7ed558ccd
            x &= ((1 << 64) - 1)
            x ^= (x >> 33)
            h = x
        return h % self.num_sets

    def _sat_inc(self, v: int) -> int:
        return v + 1 if v < self.counter_max else self.counter_max

    def _hot_try_update(self, address: int, est_cnt: int):
        if self.k == 0:
            return
        if address in self.hot_items:
            if est_cnt > self.hot_items[address]:
                self.hot_items[address] = est_cnt
            return
        if len(self.hot_items) < self.k:
            self.hot_items[address] = est_cnt
            return
        min_addr = min(self.hot_items, key=self.hot_items.get)
        min_val = self.hot_items[min_addr]
        if est_cnt > min_val:
            del self.hot_items[min_addr]
            self.hot_items[address] = est_cnt

    def update(self, address: int):
        self.total_processed += 1
        s = self._idx(address)

        hit_way = -1
        for w in range(self.num_ways):
            if self.valid[s][w] and self.tags[s][w] == address:
                hit_way = w
                break

        if hit_way >= 0:
            self.hits += 1
            new_cnt = self._sat_inc(self.cnt[s][hit_way])
            self.cnt[s][hit_way] = new_cnt
            self._hot_try_update(address, new_cnt)
            return

        self.misses += 1

        start = self.rr_ptr[s]
        free_way = -1
        for off in range(self.num_ways):
            w = (start + off) % self.num_ways
            if not self.valid[s][w]:
                free_way = w
                break

        if free_way < 0:
            # FULL -> DROP (no eviction, no allocation)
            return

        victim = free_way
        self.valid[s][victim] = True
        self.tags[s][victim] = address
        self.cnt[s][victim] = 1
        self._hot_try_update(address, 1)

        self.rr_ptr[s] = (victim + 1) % self.num_ways

    def query(self):
        return sorted(self.hot_items.items(), key=lambda x: x[1], reverse=True)

    def reset(self):
        for s in range(self.num_sets):
            for w in range(self.num_ways):
                self.valid[s][w] = False
                self.tags[s][w] = None
                self.cnt[s][w] = 0
            self.rr_ptr[s] = 0

        self.hot_items.clear()
        self.total_processed = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0