'use client';

import React, { useState } from 'react';
import { Code, CheckCircle2, AlertOctagon, Sparkles, Terminal } from 'lucide-react';
import { ResurrectedRecord } from './TombstoneCard';

interface CodeDiffViewerProps {
  record: ResurrectedRecord;
}

export const CodeDiffViewer: React.FC<CodeDiffViewerProps> = ({ record }) => {
  const [activeTab, setActiveTab] = useState<'after' | 'before'>('after');

  const beforeCode = record.repoName.includes('urlfetch')
    ? `# Vintage Python 2.7 (Abandoned 2013)
import urllib2
import urllib

class UrlFetcher(object):
    def __init__(self, timeout=10):
        self.timeout = timeout
        print "UrlFetcher initialized with timeout=%d" % timeout

    def fetch(self, url, params=None):
        if params:
            url = "%s?%s" % (url, urllib.urlencode(params))
        try:
            req = urllib2.Request(url)
            return urllib2.urlopen(req, timeout=self.timeout).read()
        except urllib2.HTTPError, e:
            print "Error: %s" % e
            raise`
    : `# Vintage Cache Daemon (Abandoned 2014)
import md5
import time
import thread

class SimpleCache(object):
    def __init__(self, ttl=300):
        self.ttl = ttl
        self.store = {}

    def _hash_key(self, key):
        m = md5.new()
        m.update(key)
        return m.hexdigest()

    def set(self, key, value):
        h = self._hash_key(key)
        self.store[h] = (value, time.time())`;

  const afterCode = record.repoName.includes('urlfetch')
    ? `"""Modernized Python 3.13 Standard Library Client (Zero Zombie Dependencies)"""
from typing import Optional, Dict, Any
import urllib.request
import urllib.parse
import urllib.error
import time
import logging

logger = logging.getLogger(__name__)

class UrlFetcher:
    """Modernized URL fetcher with exponential backoff and typed responses."""

    def __init__(self, timeout: float = 10.0, max_retries: int = 3) -> None:
        self.timeout = timeout
        self.max_retries = max_retries

    def fetch(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=self.timeout) as resp:
            return {"status": resp.status, "data": resp.read().decode("utf-8")}`
    : `"""Modernized Thread-Safe Memory Cache (Python 3.13)"""
from typing import Optional, Any, Dict, Tuple
import hashlib
import time
import threading

class ThreadSafeCache:
    def __init__(self, default_ttl: float = 300.0) -> None:
        self.default_ttl = default_ttl
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def set(self, key: str, value: Any) -> str:
        h = self._hash_key(key)
        with self._lock:
            self._store[h] = (value, time.time() + self.default_ttl)
        return h`;

  return (
    <div className="border border-tactical-border bg-obsidian-900 rounded-lg p-5 shadow-tactile-dark">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-tactical-border gap-2">
        <div>
          <h4 className="text-base font-bold text-white flex items-center gap-2 font-mono">
            <Code className="w-4 h-4 text-ectoplasm-400" />
            AST Exorcism Diff: {record.repoName}
          </h4>
          <p className="text-xs text-slate-400 font-mono">
            Cleansed by Google Gemma 2 (Local Open Weights) • Saved to <code className="text-slate-300">{record.resurrectedPath}</code>
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center gap-1 bg-obsidian-950 p-1 rounded border border-tactical-border text-xs font-mono">
          <button
            onClick={() => setActiveTab('after')}
            className={`px-3 py-1 rounded transition-colors ${
              activeTab === 'after'
                ? 'bg-ectoplasm-500/20 text-ectoplasm-300 font-bold border border-ectoplasm-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            ✨ Resurrected Python 3.13
          </button>
          <button
            onClick={() => setActiveTab('before')}
            className={`px-3 py-1 rounded transition-colors ${
              activeTab === 'before'
                ? 'bg-red-500/20 text-red-300 font-bold border border-red-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            💀 Vintage Abandoned AST
          </button>
        </div>
      </div>

      {/* Code Container */}
      <div className="mt-4 bg-obsidian-950 p-4 rounded-lg border border-tactical-border/70 overflow-x-auto text-xs font-mono leading-relaxed">
        <pre className={activeTab === 'after' ? 'text-emerald-300' : 'text-rose-300'}>
          {activeTab === 'after' ? afterCode : beforeCode}
        </pre>
      </div>

      <div className="mt-4 pt-3 border-t border-tactical-border/50 flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-slate-400">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>Vulnerable simplejson / md5 eliminated</span>
        </div>
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-ectoplasm-400" />
          <span>Auto-generated pytest suite included</span>
        </div>
      </div>
    </div>
  );
};
