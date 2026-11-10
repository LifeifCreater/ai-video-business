'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const filename = 'ai-video-feature-readiness-check.html';
const canonical = `https://framepact.jp/${filename}`;
const read = file => fs.readFileSync(path.join(root, file), 'utf8');
const html = read(filename);

test('feature readiness article is indexable with consistent structured data', () => {
  assert.equal((html.match(/<h1\b/g) || []).length, 1);
  assert.ok(html.includes(`<link rel="canonical" href="${canonical}">`));
  const robots = html.match(/<meta name="robots" content="([^"]+)">/)[1];
  assert.ok(!robots.includes('noindex'));
  const graph = JSON.parse(html.match(/<script type="application\/ld\+json">\s*([\s\S]*?)<\/script>/)[1])['@graph'];
  const article = graph.find(item => item['@type'] === 'Article');
  assert.ok(article);
  assert.equal(article.mainEntityOfPage['@id'], `${canonical}#webpage`);
  const headline = html.match(/<h1[^>]*>([^<]+)<\/h1>/)[1];
  assert.equal(article.headline, headline);
  assert.match(article.datePublished, /^\d{4}-\d{2}-\d{2}$/);
  assert.ok(html.includes(`datetime="${article.datePublished}"`));
});

test('feature readiness article is discoverable without JavaScript', () => {
  const column = read('column.html');
  assert.ok(column.includes(`class="article-card" data-category="materials" href="/${filename}"`));
  const count = (column.match(/class="article-card"/g) || []).length;
  assert.ok(column.includes(`全${count}記事｜新しい順`));
  const sitemap = read('sitemap.xml');
  assert.equal(sitemap.split(`<loc>${canonical}</loc>`).length - 1, 1);
  const stem = filename.replace(/\.html$/, '');
  const redirects = read('_redirects').split('\n');
  for (const suffix of ['', '/', '/index.html']) {
    assert.ok(redirects.includes(`/${stem}${suffix} /${filename} 301`));
  }
});

test('feature readiness contents and references resolve to unique local anchors', () => {
  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(new Set(ids).size, ids.length);
  for (const [, anchor] of html.matchAll(/href="#([^"]+)"/g)) {
    assert.ok(ids.includes(anchor), `Missing #${anchor}`);
  }
  assert.ok(html.includes('role="region" tabindex="0" aria-labelledby="checklist-caption"'));
  assert.equal((html.match(/class="related-card"/g) || []).length, 2);
  assert.ok(html.includes('id="contact" href="https://docs.google.com/forms/'));
  assert.ok(html.includes('src="/framepact-analytics.js?v=20261010"'));
});

test('feature readiness implementation keeps social promotion paused', () => {
  const shared = read('templates/article-social.html').trim();
  const block = html.match(/<!-- article-social:start -->\n([\s\S]*?)\n<!-- article-social:end -->/)[1];
  assert.equal(block, shared);
  assert.ok(!/href="https:\/\/(?:x\.com|note\.com)\//.test(html));
  const approved = read('writing/approved/WR-20261108-001-ai-video-feature-readiness-check.md');
  assert.match(approved, /^approvalStatus: approved$/m);
  assert.match(approved, /^approvalScope: article_and_site_implementation$/m);
  assert.ok(!fs.existsSync(path.join(root, 'writing/review/WR-20261108-001-ai-video-feature-readiness-check.md')));
});
