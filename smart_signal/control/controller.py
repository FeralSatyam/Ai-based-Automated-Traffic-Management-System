# smart_signal/control/controller.py

class PriorityCycleController:
    def __init__(self, approaches=["N","E","S","W"], min_green=8, max_green=30, yellow=3):
        self.approaches = approaches
        self.min_green = min_green
        self.max_green = max_green
        self.yellow = yellow
        self.priority_list = []
        self.current_idx = 0

    def start_cycle(self, counts):
        # Snapshot: sort approaches by vehicle count (descending)
        self.priority_list = sorted(
            self.approaches,
            key=lambda a: counts.get(a, 0),
            reverse=True
        )
        self.current_idx = 0

    def next_phase(self, counts):
        # If no active cycle, start one
        if not self.priority_list:
            self.start_cycle(counts)

        approach = self.priority_list[self.current_idx]
        count = counts.get(approach, 0)

        # Allocate green proportional to count, bounded
        green = max(self.min_green, min(self.max_green, count * 2))
        yellow = self.yellow

        self.current_idx += 1
        if self.current_idx >= len(self.priority_list):
            # End of cycle → reset
            self.priority_list = []

        return approach, green, yellow