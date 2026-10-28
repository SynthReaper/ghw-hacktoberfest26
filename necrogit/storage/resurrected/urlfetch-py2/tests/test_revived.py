import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch, MagicMock
from urlfetch import UrlFetcher

def test_fetcher_init():
    fetcher = UrlFetcher(timeout=5.0, max_retries=2)
    assert fetcher.timeout == 5.0
    assert fetcher.max_retries == 2

@patch("urllib.request.urlopen")
def test_fetch_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b'{"status": "resurrected"}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    fetcher = UrlFetcher()
    result = fetcher.fetch("https://api.example.com/status")

    assert result is not None
    assert result["status"] == 200
    assert "resurrected" in result["data"]

@patch("urllib.request.urlopen")
def test_fetch_with_params(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b"ok"
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    fetcher = UrlFetcher()
    result = fetcher.fetch("https://api.example.com", params={"ghost": "awakened"})
    assert result["status"] == 200
