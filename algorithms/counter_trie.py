import math
from .base import BaseTracker  

class CounterTrie(BaseTracker):
    """
    Node format:
      [sat, count, p0, p1, level]
        sat   : 0=leaf, 1=internal
        count : counter
        p0,p1 : child indices if sat==1 else -1
        level : 0 at 1GB roots; increases by 1 per split

    Thresholds:
      - levels 0..max_level-1: per_level_threshold
      - level max_level (4KB): last_level_threshold
        When a last-level leaf reaches threshold, record its PFN in hot_pfns.

    Node budget:
      - max_nodes: total entries in node pool (default 64K).
        When full, further splits are dropped (node stays leaf and keeps counting).
    """

    def __init__(
        self,
        addr_space_bytes = 64 * 1024**3,     # 64GB
        base_region_bytes = 1 * 1024**3,     # 1GB roots
        page_bytes = 4 * 1024,               # 4KB
        max_nodes = 64 * 1024,               # <= requested: 64K entries
        per_level_threshold = 10,
        last_level_threshold = 10,
        clone_on_split = False,
        k = 1024,                            # query top-k
        **kwargs
    ):
        super().__init__(**kwargs)
        self.name = (f"CounterTrie(AS={addr_space_bytes}, base={base_region_bytes}, "
                     f"page={page_bytes}, nodes={max_nodes}, "
                     f"th={per_level_threshold}/{last_level_threshold}, k={k})")

        self.addr_space_bytes = int(addr_space_bytes)
        self.base_region_bytes = int(base_region_bytes)
        self.page_bytes = int(page_bytes)
        self.max_nodes = int(max_nodes)
        self.size = int(max_nodes)
        self.per_level_threshold = int(per_level_threshold)
        self.last_level_threshold = int(last_level_threshold)
        self.clone_on_split = bool(clone_on_split)

        self.k = int(k)

        assert self.addr_space_bytes % self.base_region_bytes == 0
        assert self.base_region_bytes % self.page_bytes == 0

        ratio = self.base_region_bytes // self.page_bytes
        assert ratio & (ratio - 1) == 0, "base_region_bytes/page_bytes must be power of two"
        self.max_level = ratio.bit_length() - 1  # 1GB->4KB => 18

        self.num_roots = self.addr_space_bytes // self.base_region_bytes
        assert self.num_roots <= self.max_nodes, "max_nodes must be >= num_roots"

        self.reset()

    def reset(self):
        # node: [sat, count, p0, p1, level]
        self.nodes = [[0, 0, -1, -1, 0] for _ in range(self.max_nodes)]
        self.max_ptr = self.num_roots

        for i in range(self.num_roots):
            self.nodes[i] = [0, 0, -1, -1, 0]

        self.hot_pfns = set()
        self.hot_pfn_cnt = {}  # pfn -> count
        self.reported_leaf = [False] * self.max_nodes
        

    def _root(self, addr: int) -> int:
        return addr // self.base_region_bytes  # 0..num_roots-1

    def _dir_within_root(self, addr: int, root_base: int, level: int) -> int:
        """
        Decide left/right inside a 1GB root using binary halving.
          level=0: 1GB -> 512MB
          level=1: 512MB -> 256MB
          ...
        """
        sub_size = self.base_region_bytes >> level
        half = sub_size >> 1
        off = addr - root_base
        in_sub = off & (sub_size - 1)
        return 1 if in_sub >= half else 0

    def _threshold(self, level: int) -> int:
        return self.last_level_threshold if level >= self.max_level else self.per_level_threshold

    def update(self, address: int):
        pfn = int(address)
        addr = pfn << 12 
        if addr < 0 or addr >= self.addr_space_bytes:
            return

        r = self._root(addr)
        root_base = r * self.base_region_bytes

        idx = r
        while True:
            sat, cnt, p0, p1, lvl = self.nodes[idx]

            if sat == 1:
                # internal: chase
                if lvl >= self.max_level:
                    # defensive fallback: count here
                    self.nodes[idx][1] = cnt + 1
                    return
                d = self._dir_within_root(addr, root_base, lvl)
                idx = p1 if d else p0
                if idx < 0:
                    return
                continue

            # leaf: update
            cnt += 1
            self.nodes[idx][1] = cnt

            th = self._threshold(lvl)

            # last-level behavior: record hot PFN
            if lvl == self.max_level and cnt >= th:
                self.hot_pfns.add(pfn)
                self.hot_pfn_cnt[pfn] = cnt
                self.reported_leaf[idx] = True
                return

            # split if needed
            if cnt >= th and lvl < self.max_level:
                # drop split if node pool is full (keep as leaf, keep counting)
                if self.max_ptr + 1 >= self.max_nodes:
                    return

                c0 = self.max_ptr
                c1 = self.max_ptr + 1
                self.max_ptr += 2

                init = cnt if self.clone_on_split else 0
                child_lvl = lvl + 1

                self.nodes[c0] = [0, init, -1, -1, child_lvl]
                self.nodes[c1] = [0, init, -1, -1, child_lvl]

                self.reported_leaf[c0] = False
                self.reported_leaf[c1] = False

                # make current node internal
                self.nodes[idx][0] = 1
                self.nodes[idx][2] = c0
                self.nodes[idx][3] = c1

                # split 직후 이번 access 1회를 child에 즉시 반영
                # parent의 lvl 기준으로 left/right 결정해야 함 (이번 split이 lvl에서 일어났으니까)
                d = self._dir_within_root(addr, root_base, lvl)
                child = c1 if d else c0
                child_cnt = self.nodes[child][1] + 1
                self.nodes[child][1] = child_cnt

                # split으로 인해 child가 max_level이 되는 특이 케이스면 hot 처리까지 여기서 해도 됨
                if child_lvl == self.max_level and child_cnt >= self._threshold(child_lvl):
                    self.hot_pfns.add(pfn)
                    self.hot_pfn_cnt[pfn] = child_cnt
                    self.reported_leaf[child] = True
                return
            
            return
        
    def query(self): 
        kk = min(self.k, len(self.hot_pfn_cnt))
        res = sorted(self.hot_pfn_cnt.items(), key=lambda x: x[1], reverse=True)[:kk]
        return res