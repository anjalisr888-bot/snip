import pytest

from app.cache import LRUCache


def test_get_missing_returns_none():
    c = LRUCache(2)
    assert c.get("a") is None


def test_put_and_get():
    c = LRUCache(2)
    c.put("a", 1)
    assert c.get("a") == 1


def test_evicts_least_recently_used():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)  # "a" is the oldest, so it is evicted
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_get_refreshes_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")      # "a" is now the most recent
    c.put("c", 3)   # so "b" is evicted instead
    assert c.get("b") is None
    assert c.get("a") == 1


def test_update_existing_key():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("a", 10)
    assert c.get("a") == 10
    assert len(c) == 1


def test_capacity_one():
    c = LRUCache(1)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") is None
    assert c.get("b") == 2


def test_invalid_capacity():
    with pytest.raises(ValueError):
        LRUCache(0)