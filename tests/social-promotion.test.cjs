'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');

const pages = fs.readdirSync('.').filter(name => name.endsWith('.html'));
const pausedDomain = /(?:https?:)?\/\/(?:[a-z0-9-]+\.)*(?:x\.com|twitter\.com|t\.co|note\.com)(?=[/?#\s"'<>]|$)/i;

test('public pages, scripts, shared template and redirects do not promote paused social destinations', () => {
  const resources = fs.readdirSync('.').filter(name => /\.(html|js)$/.test(name));
  resources.push('templates/article-social.html', '_redirects');
  for (const path of resources) {
    assert.doesNotMatch(fs.readFileSync(path, 'utf8'), pausedDomain, path);
  }
});

test('paused article footer slot contains no empty FOLLOW section or interactive elements', () => {
  const template = fs.readFileSync('templates/article-social.html', 'utf8').trim();
  assert.match(template, /^<!--[\s\S]*-->$/);
  assert.doesNotMatch(template, /<(?:a|h4|div|ul)\b/i);
  let managedPages = 0;
  for (const path of pages) {
    const html = fs.readFileSync(path, 'utf8');
    const slots = [...html.matchAll(/<!-- article-social:start -->\n([\s\S]*?)\n<!-- article-social:end -->/g)];
    if (!slots.length) continue;
    managedPages++;
    assert.equal(slots.length, 1, path);
    assert.equal(slots[0][1], template, path);
    assert.doesNotMatch(html, /<h4>FOLLOW<\/h4>/i, path);
  }
  assert.ok(managedPages >= 18, 'existing article footers must remain managed');
});

test('old social shortcuts stay on the site, and no public link points to those shortcuts', () => {
  const redirects = fs.readFileSync('_redirects', 'utf8');
  for (const alias of ['x', 'note']) {
    assert.match(redirects, new RegExp('^/' + alias + '\\s+/column\\.html\\s+302\\s*$', 'm'));
  }
  for (const path of pages) {
    assert.doesNotMatch(fs.readFileSync(path, 'utf8'), /<a\b[^>]*href=["'](?:https?:\/\/framepact\.jp)?\/(?:x|note)(?:[/?#][^"']*)?["']/i, path);
  }
});

test('column, inquiry, privacy navigation and sharing metadata remain intact', () => {
  const home = fs.readFileSync('index.html', 'utf8');
  for (const destination of ['column.html', 'privacy.html', 'https://docs.google.com/forms/']) {
    assert.ok(home.includes(destination), destination);
  }
  // Twitter card metadata describes a shared preview; it is not a promotional link.
  assert.match(home, /name="twitter:card"/);
  const column = fs.readFileSync('column.html', 'utf8');
  assert.equal([...column.matchAll(/<a\b[^>]*class="article-card"/g)].length, 18);
});
