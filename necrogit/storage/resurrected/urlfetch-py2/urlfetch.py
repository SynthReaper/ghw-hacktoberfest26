"""
urlfetch — Modernized, high-resilience HTTP client.
Resurrected by NecroGit for Hacktoberfest 2026 Week 4 ("Ghost in the Machine").
Modern Python 3.13 + Standard Library with zero zombie dependencies.
"""

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
        logger.info("UrlFetcher initialized with timeout=%.1f, max_retries=%d", timeout, max_retries)

    def fetch(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Executes a GET request with query params and automatic retry logic."""
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                logger.debug("Requesting %s (attempt %d/%d)", url, attempt + 1, self.max_retries)
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "NecroGit-UrlFetcher/1.0.0 (Python 3.13; Hardened)"}
                )
                start_time = time.perf_counter()
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    content = response.read().decode("utf-8", errors="replace")
                    elapsed = time.perf_counter() - start_time
                    return {
                        "status": response.status,
                        "data": content,
                        "elapsed": round(elapsed, 4),
                        "url": url,
                    }
            except urllib.error.HTTPError as e:
                logger.warning("HTTP error %d for %s", e.code, url)
                last_error = e
                if e.code in (400, 401, 403, 404):
                    raise
            except urllib.error.URLError as e:
                logger.warning("Network failure: %s (attempt %d)", e.reason, attempt + 1)
                last_error = e
                time.sleep(0.5 * (2 ** attempt))
            except Exception as e:
                logger.error("Unexpected error during fetch: %s", e)
                raise

        if last_error:
            raise last_error
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetcher = UrlFetcher()
    print("NecroGit UrlFetcher 1.0.0 online.")
