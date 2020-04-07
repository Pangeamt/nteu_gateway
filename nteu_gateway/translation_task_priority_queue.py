import itertools
import heapq


class TranslationTaskPriorityQueue:
    REMOVED = 'removed'

    def __init__(self):
        self._finder = {}
        self._counter = itertools.count()
        self._q = []

    def add_task(self, task):
        count = next(self._counter)
        priority = task.priority
        entry = (priority, count, task)
        self._finder[task] = entry
        heapq.heappush(self._q, entry)

    def remove_task(self, task):
        entry = self._finder.pop(task)
        entry[-1] = self.REMOVED

    def pop_task(self):
        while self._q:
            priority, count, task = heapq.heappop(self._q)
            if task is not self.REMOVED:
                del self._finder[task]
                return task
        raise KeyError('Pop from an empty priority queue')

    def is_empty(self):
        if not self._q:
            return True
        return False