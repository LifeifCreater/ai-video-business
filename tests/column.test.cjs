'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const index=fs.readFileSync('column.html','utf8');
const release=JSON.parse(fs.readFileSync('writing/releases/columns-20261031.json','utf8'));
function graphs(text){return [...text.matchAll(/<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g)].flatMap(m=>{const x=JSON.parse(m[1]);return x['@graph']||[x];});}
test('all 18 article links are in HTML and initially readable without JS',()=>{
 const cards=[...index.matchAll(/<a\b[^>]*class="article-card"[^>]*>/g)].map(m=>m[0]);
 assert.equal(cards.length,18);
 cards.forEach(c=>assert.doesNotMatch(c,/\bhidden\b/));
 assert.match(index,/id="column-search"/);assert.match(index,/id="column-category"/);
 assert.match(index,/id="column-all"/);assert.match(index,/data-column-controls hidden/);
});
test('five reviewed sources have real HTML, correct metadata and current publication dates',()=>{
 assert.equal(release.articles.length,5);
 for(const a of release.articles){
  const text=fs.readFileSync(a.url.slice(1),'utf8');
  assert.ok(index.includes('href="'+a.url+'"'),a.id);
  assert.ok(fs.readFileSync('sitemap.xml','utf8').includes('https://framepact.jp'+a.url));
  const article=graphs(text).find(x=>x['@type']==='Article');
  assert.equal(article.headline,a.title);assert.equal(article.datePublished,'2026-10-31');
  assert.equal(article.dateModified,'2026-10-31');
  assert.ok(text.includes('href="https://framepact.jp'+a.url+'"'));
  assert.equal((text.match(/<h1\b/g)||[]).length,1);
  assert.doesNotMatch(text,/編集管理メモ|原稿管理情報|title案|description案|writing\/inbox/);
  assert.match(text,/class="table-wrap"/);assert.match(text,/class="related-card"/);
  assert.match(text,/id="contact"/);
 }
});
test('public HTML and shared navigation have no note promotion links or profile references',()=>{
 for(const name of [...fs.readdirSync('.').filter(p=>/\.(html|js)$/.test(p)),'templates/article-social.html','_redirects']){
  assert.doesNotMatch(fs.readFileSync(name,'utf8'),/https?:\/\/(?:www\.)?note\.com\b/i,name);
 }
});
test('progressive filtering is local and hidden cards cannot override the hidden attribute',()=>{
 const js=fs.readFileSync('framepact-column.js','utf8');
 assert.match(js,/step=6/);assert.match(js,/function fallback/);
 assert.doesNotMatch(js,/fetch\(|XMLHttpRequest|sendBeacon|gtag\(/);
 const css=fs.readFileSync('framepact-column.css','utf8');
 assert.match(css,/\.article-card\[hidden\]/);assert.match(css,/display:none!important/);
});
