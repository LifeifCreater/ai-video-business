#!/usr/bin/env python3
"""Integration test canonical routes using a running Wrangler or production origin."""
import os
import subprocess
import sys
import time
from pathlib import Path

origin = sys.argv[1].rstrip('/')
root = Path(__file__).resolve().parent.parent
query = '?routing-check=' + os.environ.get('GITHUB_SHA', 'local')


def fetch(route, timeout=20):
    # Use the same public HTTP transport as check-production.py.
    result = subprocess.run(
        ['curl', '-fsSL', '--connect-timeout', '5', '--max-time', str(timeout),
         '--max-redirs', '5', '-H', 'Cache-Control: no-cache',
         '-w', '\n%{url_effective}', origin + route + query],
        capture_output=True, check=True, timeout=timeout + 5,
    )
    return result.stdout.decode('utf-8').rsplit('\n', 1)


for attempt in range(60):
    try:
        fetch('/', 2)
        break
    except Exception:
        if attempt == 59:
            raise
        time.sleep(1)

for page in sorted(root.glob('*.html')):
    if page.name == '404.html':
        continue
    canonical = '/' if page.name == 'index.html' else '/' + page.name
    aliases = ['/index', '/index.html'] if page.name == 'index.html' else ['/' + page.stem, '/' + page.stem + '/']
    for route in [canonical, *aliases]:
        html, effective_url = fetch(route)
        assert effective_url == origin + canonical + query, (route, effective_url)
        assert html.replace('\r\n', '\n').strip() == page.read_text().strip(), route
print('Canonical routes, aliases, query strings and page contents verified.')
