'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = name => fs.readFileSync(path.join(root, name), 'utf8');
const primaryPages = [
  'corporate-pr-video.html',
  'corporate-ai-video.html',
  'no-material-ai-video.html',
  'training-video.html',
  'event-video.html',
];
const canonical = name => `https://framepact.jp/${name}`;

function firstMatch(html, regex, name) {
  const match = regex.exec(html);
  assert.ok(match, `missing ${name}`);
  return match[1];
}

function meta(html, attribute, value) {
  const tags = html.match(/<meta\s[^>]*>/g) || [];
  const tag = tags.find(t => t.includes(`${attribute}="${value}"`));
  assert.ok(tag, `missing meta ${attribute}=${value}`);
  return firstMatch(tag, /\bcontent="([^"]*)"/, `content for ${value}`);
}

test('homepage exposes all six service destinations as crawlable links', () => {
  const html = read('index.html');
  const entries = [...html.matchAll(/<a\s+href="(\/[^"#]+\.html)"\s+data-service="(\d+)"/g)];
  assert.equal(entries.length, 6);
  const paths = [
    '/corporate-pr-video.html',
    '/recruit-video.html',
    '/training-video.html',
    '/corporate-ai-video.html',
    '/event-video.html',
    '/no-material-ai-video.html',
  ];
  for (const [index, entry] of entries.entries()) {
    assert.equal(Number(entry[2]), index, 'service modal index must match its destination');
    assert.equal(entry[1], paths[index]);
    assert.ok(fs.existsSync(path.join(root, entry[1].slice(1))));
  }
  assert.match(read('framepact-cinema.js'), /if\(b\.matches\('a'\)\)e\.preventDefault\(\)/);
  assert.match(read('framepact-cinema.css'), /\.service-list>a\{/);
});

test('priority service pages have consistent canonical, social and structured metadata', () => {
  for (const page of primaryPages) {
    const html = read(page);
    const title = firstMatch(html, /<title>([^<]+)<\/title>/, `${page} title`);
    const description = meta(html, 'name', 'description');
    assert.equal(firstMatch(html, /<link\s+rel="canonical"\s+href="([^"]+)"/, `${page} canonical`), canonical(page));
    assert.equal(meta(html, 'property', 'og:url'), canonical(page));
    assert.equal(meta(html, 'property', 'og:title'), title);
    assert.equal(meta(html, 'name', 'twitter:title'), title);
    assert.equal(meta(html, 'property', 'og:description'), description);
    assert.equal(meta(html, 'name', 'robots').startsWith('index, follow'), true);
    assert.equal((html.match(/<h1(?:\s|>)/g) || []).length, 1, `${page} has one H1`);
    const json = firstMatch(html, /<script type="application\/ld\+json">([\s\S]+?)<\/script>/, `${page} schema`);
    const webpage = JSON.parse(json)['@graph'].find(item => item['@type'] === 'WebPage');
    assert.ok(webpage, `${page} WebPage schema exists`);
    assert.equal(webpage.url, canonical(page));
    assert.equal(webpage.name, title);
    assert.equal(webpage.description, description);
  }
});

test('updated service pages show only the approved price plans and correct conditions', () => {
  for (const page of primaryPages) {
    const html = read(page);
    assert.match(html, /15万円〜/u, `${page}: simple plan`);
    assert.match(html, /30秒以内/u, `${page}: simple plan duration`);
    assert.match(html, /税抜/u, `${page}: taxes`);
    assert.match(html, /href="\/ai-video-price\.html"/, `${page}: detailed pricing link`);
    assert.match(html, /href="\/#works"/, `${page}: showreel link`);
  }
  assert.match(read('training-video.html'), /長尺[^<]*個別にお見積もり/u);
});

test('priority pages link to the existing form and keep tracking as an outbound click', () => {
  const formPath = /https:\/\/docs\.google\.com\/forms\/d\/e\/1FAIpQLSeS-G-8U9p5-zMiFGaH3Y0TZjswVbvKOLl1Rg1_uK2GKw0blg\/viewform/;
  for (const page of primaryPages) assert.match(read(page), formPath, `${page}: contact form`);
  const analytics = read('framepact-analytics.js');
  assert.match(analytics, /contact_form_click/);
  assert.doesNotMatch(analytics, /['"]generate_lead['"]/);
});

test('modified pages have fresh sitemap lastmod entries', () => {
  const sitemap = read('sitemap.xml');
  const pages = ['index.html', ...primaryPages];
  for (const page of pages) {
    const url = page === 'index.html' ? 'https://framepact.jp/' : canonical(page);
    assert.ok(sitemap.includes(`<loc>${url}</loc>\n    <lastmod>2026-10-25</lastmod>`), `${url}: sitemap lastmod`);
  }
});

test('all published pages have reachable local references and valid section targets', () => {
  const pages = fs.readdirSync(root).filter(name => name.endsWith('.html'));
  const redirects = read('_redirects');
  for (const page of pages) {
    const html = read(page);
    const urls = [...html.matchAll(/\b(?:href|src|poster)=["']([^"']+)["']/g)].map(match => match[1]);
    for (const raw of urls) {
      if (raw.startsWith('data:') || raw.startsWith('mailto:') || raw.startsWith('tel:') || raw.startsWith('javascript:') || raw.includes("' +")) continue;
      const url = new URL(raw, canonical(page));
      if (url.origin !== 'https://framepact.jp') continue;
      const file = decodeURIComponent(url.pathname.slice(1)) || 'index.html';
      const filePath = path.join(root, file);
      const redirected = redirects.split('\n').some(line => line.startsWith(`/${file} `));
      assert.ok(fs.existsSync(filePath) || redirected, `${page}: missing local target ${raw}`);
      if (url.hash && (file === 'index.html' || file.endsWith('.html')) && fs.existsSync(filePath)) {
        const targetHtml = read(file);
        const fragment = decodeURIComponent(url.hash.slice(1));
        assert.ok(targetHtml.includes(`id="${fragment}"`) || targetHtml.includes(`id='${fragment}'`), `${page}: missing fragment ${raw}`);
      }
    }
  }
});

test('XML sitemap lists exactly the indexable HTML pages', () => {
  const htmlFiles = fs.readdirSync(root).filter(name => name.endsWith('.html'));
  const indexable = htmlFiles.filter(name => name !== '404.html' && !/<meta\s+name="robots"\s+content="noindex/i.test(read(name)));
  const sitemap = [...read('sitemap.xml').matchAll(/<loc>https:\/\/framepact\.jp(\/[^<]*)<\/loc>/g)]
    .map(match => match[1] === '/' ? 'index.html' : match[1].slice(1));
  assert.deepEqual(sitemap.slice().sort(), indexable.slice().sort());
});
