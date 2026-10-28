# -*- coding: utf-8 -*-
"""
CacheDaemon v0.1 — In-Memory Key-Value LRU Cache
Abandoned in 2014.
"""

import md5
import time
import thread

class SimpleCache(object):
    def __init__(self, ttl=300):
        self.ttl = ttl
        self.store = {}
        print "Cache initialized with TTL=%d" % ttl

    def _hash_key(self, key):
        m = md5.new()
        m.update(key)
        return m.hexdigest()

    def set(self, key, value):
        h = self._hash_key(key)
        self.store[h] = (value, time.time())
        print "Set key=%s hash=%s" % (key, h)

    def get(self, key):
        h = self._hash_key(key)
        if h in self.store:
            val, ts = self.store[h]
            if time.time() - ts < self.ttl:
                return val
            else:
                del self.store[h]
                print "Evicted expired key %s" % key
        return None
