import pytest
from daemon import ThreadSafeCache

def test_cache_set_get():
    cache = ThreadSafeCache(default_ttl=10.0)
    cache.set("spirit", "active")
    assert cache.get("spirit") == "active"

def test_cache_expiry():
    cache = ThreadSafeCache(default_ttl=0.01)
    cache.set("fleeting", "ghost")
    import time; time.sleep(0.02)
    assert cache.get("fleeting") is None
