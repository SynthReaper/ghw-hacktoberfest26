"""
CacheDaemon v1.0.0 — Modernized High-Performance In-Memory Cache
Resurrected by NecroGit for Hacktoberfest 2026 Week 4.
Modern Python 3.13 + hashlib + threading.Lock.
"""

from typing import Optional, Any, Dict, Tuple
import hashlib
import time
import threading

class ThreadSafeCache:
    """Thread-safe key-value cache with TTL eviction and SHA256 key hashing."""

    def __init__(self, default_ttl: float = 300.0) -> None:
        self.default_ttl = default_ttl
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def _hash_key(self, key: str) -> str:
        """Computes secure SHA256 key hash (replacing vulnerable md5)."""
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> str:
        """Stores a key-value pair with TTL."""
        h = self._hash_key(key)
        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        with self._lock:
            self._store[h] = (value, expiry)
        return h

    def get(self, key: str) -> Optional[Any]:
        """Retrieves an item if not expired."""
        h = self._hash_key(key)
        with self._lock:
            if h in self._store:
                val, expiry = self._store[h]
                if time.time() < expiry:
                    return val
                del self._store[h]
        return None

    def size(self) -> int:
        """Returns count of active keys in cache."""
        with self._lock:
            return len(self._store)
