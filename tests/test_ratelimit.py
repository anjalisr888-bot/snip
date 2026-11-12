import pytest

from app.ratelimit import RateLimiter


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


def test_allows_up_to_capacity():
    clock = FakeClock()
    rl = RateLimiter(capacity=3, refill_rate=1, clock=clock)
    assert rl.allow("a")[0] is True
    assert rl.allow("a")[0] is True
    assert rl.allow("a")[0] is True
    assert rl.allow("a")[0] is False


def test_refills_over_time():
    clock = FakeClock()
    rl = RateLimiter(capacity=2, refill_rate=1, clock=clock)
    rl.allow("a")
    rl.allow("a")
    assert rl.allow("a")[0] is False
    clock.advance(1)
    assert rl.allow("a")[0] is True


def test_never_exceeds_capacity():
    clock = FakeClock()
    rl = RateLimiter(capacity=2, refill_rate=1, clock=clock)
    clock.advance(1000)  # long idle time
    assert rl.allow("a")[0] is True
    assert rl.allow("a")[0] is True
    assert rl.allow("a")[0] is False  # still only 2, not 1000


def test_keys_are_independent():
    clock = FakeClock()
    rl = RateLimiter(capacity=1, refill_rate=1, clock=clock)
    assert rl.allow("a")[0] is True
    assert rl.allow("a")[0] is False
    assert rl.allow("b")[0] is True


def test_retry_after():
    clock = FakeClock()
    rl = RateLimiter(capacity=1, refill_rate=2, clock=clock)
    rl.allow("a")
    allowed, retry = rl.allow("a")
    assert allowed is False
    assert retry == pytest.approx(0.5)


def test_invalid_config():
    with pytest.raises(ValueError):
        RateLimiter(capacity=0, refill_rate=1)