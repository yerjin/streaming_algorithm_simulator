import random
import math
from .base import BaseTracker


class StickySampling(BaseTracker):
    def __init__(self, s, epsilon, delta, k, max_entries=None, **kwargs):
        super().__init__(**kwargs)
        self.name = f"StickySampling(s={s}, e={epsilon}, d={delta}, k={k})"

        self.s = s
        self.e = epsilon
        self.delta = delta
        self.k = int(k)

        # phase parameter
        self.t = (1.0 / epsilon) * math.log(1.0 / (s * delta)) 

        self.r = 1
        self.sample_cnt = 0
        self.total_processed = 0

        if max_entries is None:
            max_entries = math.ceil(2 * self.t)
        self.max_entries = max(1, int(max_entries))

        self.size = self.max_entries
        self.counts = {}

    def _phase_threshold(self):
        thr = 2 * self.t if self.r <= 2 else self.t * self.r
        return int(math.ceil(thr))

    def update(self, address):
        self.total_processed += 1 # epoch이 오면 초기화됨, 용도는 나중에 hot한거 return할 때 쓰임
        self.sample_cnt += 1      # Sample되어서 table에 hit/alloc한거 아니고 받은 총 request 수임 (prune시 초기화됨)

        # 1) hit
        if address in self.counts:
            self.counts[address] += 1
        else:
            # 2) miss
            if self.r == 1 or random.random() < (1.0 / self.r):
                if len(self.counts) < self.max_entries:
                    self.counts[address] = 1
                else:
                    pass  # HW budget full > drop

        # 3) phase end (adjust sampling rate + pruning)
        if self.sample_cnt >= self._phase_threshold():
            self._adjust_sampling_rate()

    def _adjust_sampling_rate(self):
        self.r *= 2
        self.sample_cnt = 0

        items_to_remove = []
        for addr in list(self.counts.keys()):
            count = self.counts[addr]

            # Coin toss를 실패할때까지 해서, count를 binomial distribution 따라 깎음.
            while count > 0:
                if random.random() < 0.5:
                    break
                count -= 1

            if count > 0:
                self.counts[addr] = count
            else:
                items_to_remove.append(addr)

        for addr in items_to_remove:
            del self.counts[addr]

    def query(self):
        #self.threshold = int((self.s - self.e) * self.total_processed)
        #res = [(addr, cnt) for addr, cnt in self.counts.items() if cnt >= self.threshold]
        #res.sort(key=lambda x: x[1], reverse=True)
        #return res

        kk = min(self.k, len(self.counts))
        return sorted(self.counts.items(), key=lambda x: x[1], reverse=True)[:kk]

    def reset(self):
        self.counts.clear()
        self.r = 1
        self.sample_cnt = 0
        self.total_processed = 0
        
