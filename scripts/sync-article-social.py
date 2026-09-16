#!/usr/bin/env python3
"""Keep article social links static (no client-side rendering or build dependency)."""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
START = '<!-- article-social:start -->'
END = '<!-- article-social:end -->'


def article_pages():
    return sorted(p for p in ROOT.glob('*.html') if re.search(r'"@type"\s*:\s*"Article"', p.read_text()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    block = START + '\n' + (ROOT / 'templates/article-social.html').read_text().strip() + '\n' + END
    stale = []
    for page in article_pages():
        html = page.read_text()
        assert 'id="contact"' in html and 'https://docs.google.com/forms/' in html, f'{page.name}: missing contact CTA'
        assert 'class="related-card"' in html, f'{page.name}: missing related links'
        assert 'href="/column.html"' in html, f'{page.name}: missing column link'
        if START in html:
            assert html.count(START) == html.count(END) == 1, page.name
            updated = re.sub(re.escape(START) + r'.*?' + re.escape(END), lambda _: block, html, flags=re.S)
        else:
            assert html.count('<div class="footer-links">') == 1, page.name
            updated = html.replace('<div class="footer-links">', '<div class="footer-links">\n' + block + '\n')
        if updated != html:
            stale.append(page.name)
            if not args.check:
                page.write_text(updated)
    if args.check and stale:
        raise SystemExit('Run python3 scripts/sync-article-social.py: ' + ', '.join(stale))
    print(f'Article social links verified ({len(article_pages())} pages).')


if __name__ == '__main__':
    main()
