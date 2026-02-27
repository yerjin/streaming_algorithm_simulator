from collections import Counter
from .base import BaseTracker

class Oracle(BaseTracker):
    """
    Exact (oracle) frequency counter:
    - update(item): increment exact count for item
    - query(): return (item, count) sorted by count desc
    - reset(): clear all state
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "OracleCounter"
        self.counter = Counter()
        self.threshold = 0
        self.size = 0
    def update(self, item):
        self.counter[item] += 1

    def query(self):
        return self.counter.most_common()

    def reset(self):
        self.counter.clear()