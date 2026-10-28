# -*- coding: utf-8 -*-
"""
urlfetch — Lightweight HTTP retrieval utility.
Copyright (c) 2012 Original Author. Abandoned in 2013.
VINTAGE PYTHON 2 CODEBASE.
"""

import urllib2
import urllib
import sys
import time

class UrlFetcher(object):
    def __init__(self, timeout=10, max_retries=3):
        self.timeout = timeout
        self.max_retries = max_retries
        print "UrlFetcher initialized with timeout=%d" % timeout

    def fetch(self, url, params=None):
        if params:
            encoded_params = urllib.urlencode(params)
            url = "%s?%s" % (url, encoded_params)

        for attempt in xrange(self.max_retries):
            try:
                print "Attempting GET request to %s (attempt %d)" % (url, attempt + 1)
                req = urllib2.Request(url, headers={'User-Agent': 'UrlFetcher/0.1'})
                response = urllib2.urlopen(req, timeout=self.timeout)
                data = response.read()
                return {
                    'status': response.getcode(),
                    'data': unicode(data, 'utf-8', errors='ignore'),
                    'elapsed': 0.12
                }
            except urllib2.HTTPError, e:
                print "HTTP Error encountered: %d - %s" % (e.code, e.msg)
                if attempt == self.max_retries - 1:
                    raise
            except urllib2.URLError, e:
                print "URL Error: %s" % e.reason
                time.sleep(1)
            except Exception, e:
                print "Unexpected error: %s" % str(e)
                raise

        return None

if __name__ == "__main__":
    fetcher = UrlFetcher()
    print "Ready to fetch."
