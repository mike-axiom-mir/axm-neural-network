from collections import deque


class LocalQueue:
    def __init__(self, limit: int = 32):
        self.limit = limit
        self.items = deque()

    def put(self, item):
        if len(self.items) >= self.limit:
            return False
        self.items.append(item)
        return True

    def get(self):
        if not self.items:
            return None
        return self.items.popleft()
