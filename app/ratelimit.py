import threading
import time


class RateLimiter:
    def __init__(self, capacity: float, refill_rate: float, clock=time.monotonic):
        if capacity < 1 or refill_rate <= 0:
            raise ValueError("capacity must be >= 1 and refill_rate > 0")
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.clock = clock
        self.buckets = {}  # key -> [tokens, last_timestamp]
        self.lock = threading.Lock()

    def allow(self, key: str):
        """Return (allowed, retry_after_seconds)."""
        with self.lock:
            now = self.clock()

            if key not in self.buckets:
                self.buckets[key] = [self.capacity, now]

            tokens, last = self.buckets[key]
            tokens = min(self.capacity, tokens + (now - last) * self.refill_rate)

            if tokens >= 1:
                self.buckets[key] = [tokens - 1, now]
                return True, 0.0

            self.buckets[key] = [tokens, now]
            return False, (1 - tokens) / self.refill_rate