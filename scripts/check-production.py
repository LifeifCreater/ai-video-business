#!/usr/bin/env python3
"""Wait for the homepage and every article to match this checkout in production."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import os
import subprocess
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('article_social', ROOT / 'scripts/sync-article-social.py')
social = importlib.util.module_from_spec(spec)
spec.loader.exec_module(social)


def matches(page):
    route = '/' if page.name == 'index.html' else '/' + page.name
    url = 'https://framepact.jp' + route + '?deploy-check=' + os.environ.get('GITHUB_SHA', 'manual')
    try:
        # Preserve the existing smoke check's curl transport and certificate handling.
        response = subprocess.run(
            ['curl', '-fsSL', '--connect-timeout', '10', '--max-time', '20',
             '-H', 'Cache-Control: no-cache', url],
            check=True, capture_output=True, timeout=25,
        )
        live = response.stdout.decode('utf-8').replace('\r\n', '\n').strip()
        return page.name, live == page.read_text().strip()
    except Exception as error:
        print(f'{page.name}: {type(error).__name__}', flush=True)
        return page.name, False


def main():
    pages = [ROOT / 'index.html', *social.article_pages()]
    deadline = time.monotonic() + 540
    attempt = 0
    while time.monotonic() < deadline:
        attempt += 1
        with ThreadPoolExecutor(max_workers=9) as pool:
            pending = [name for name, ok in pool.map(matches, pages) if not ok]
        if not pending:
            print(f'Production matches checkout ({len(pages)} pages).', flush=True)
            return
        print(f'Deployment check {attempt}; waiting for: {", ".join(pending)}', flush=True)
        time.sleep(min(15, max(0, deadline - time.monotonic())))
    raise SystemExit('Production did not match the checkout before the deployment deadline.')


if __name__ == '__main__':
    main()
