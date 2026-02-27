from abc import ABC, abstractmethod

class BaseTracker(ABC):
    def __init__(self, **kwargs):
        self.name = "Base"

    @abstractmethod
    def update(self, item):
        pass

    @abstractmethod
    def query(self, k):
        # return: List of (item, estimated_count)
        pass

    @abstractmethod
    def reset(self):
        pass
