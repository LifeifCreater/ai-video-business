'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const pages=fs.readdirSync('.').filter(p=>p.endsWith('.html')&&!['preview-home.html','analytics-owner.html'].includes(p));
test('all public pages load the shared responsive stylesheet exactly once',()=>{
  assert.ok(pages.length>0);
  for(const name of pages){
    const source=fs.readFileSync(name,'utf8');
    assert.equal((source.match(/href="\/framepact-responsive\.css\?v=20261031"/g)||[]).length,1,name);
    assert.match(source,/<meta\s+name="viewport"\s+content="width=device-width,\s*initial-scale=1(?:\.0)?"/,name);
  }
});
test('content is visible by default without scripts or IntersectionObserver',()=>{
  for(const name of pages){
    const html=fs.readFileSync(name,'utf8');
    const styles=[...html.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map(x=>x[1]);
    for(const css of styles){
      for(const rule of css.matchAll(/\.(?:reveal|process-step)\s*\{([^}]*)\}/g)){
        assert.doesNotMatch(rule[1],/opacity\s*:\s*0(?:\s*;|\s*$)/,`${name}: hidden content default`);
      }
    }
  }
});
test('the complete column list is not a single visibility-triggered animation',()=>{
  const html=fs.readFileSync('column.html','utf8');
  assert.match(html,/class="article-list"/);
  assert.doesNotMatch(html,/class="article-list reveal/);
  assert.ok((html.match(/class="article-card"/g)||[]).length>0);
});
test('foldable safeguards reflow content without device sniffing or global clipping',()=>{
  const css=fs.readFileSync('framepact-responsive.css','utf8');
  assert.match(css,/repeat\(auto-fit, minmax\(min\(100%, 20rem\), 1fr\)\)/);
  assert.match(css,/grid-template-rows: auto minmax\(0, 1fr\) auto/);
  assert.match(css,/overflow-wrap: anywhere/);
  assert.match(css,/safe-area-inset-right/);
  assert.doesNotMatch(css,/overflow-x:\s*hidden/);
});
