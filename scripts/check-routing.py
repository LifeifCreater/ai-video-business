#!/usr/bin/env python3
"""Integration test canonical routes using a running Wrangler or production origin."""
import sys
import time
import urllib.request
from pathlib import Path

origin = sys.argv[1].rstrip('/')
root = Path(__file__).resolve().parent.parent
for attempt in range(60):
    try:
        with urllib.request.urlopen(origin + '/', timeout=2) as response:
            assert response.status == 200
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
        with urllib.request.urlopen(origin + route + '?routing-check=1', timeout=20) as response:
            assert response.status == 200, route
            assert response.geturl() == origin + canonical + '?routing-check=1', (route, response.geturl())
            html = response.read().decode()
            assert html.strip() == page.read_text().strip(), route
print('Canonical routes, aliases, query strings and page contents verified.')
