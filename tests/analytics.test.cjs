const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('framepact-analytics.js', 'utf8');
const FORM = 'https://docs.google.com/forms/d/e/1FAIpQLSeS-G-8U9p5-zMiFGaH3Y0TZjswVbvKOLl1Rg1_uK2GKw0blg/viewform';
function boot({host='framepact.jp', path='/', exclude=false, blocked=false, saved=null, ref='', search=''}={}) {
  const memory = new Map(exclude ? [['framepact.analytics.internal','1']] : []);
  const session = new Map(saved ? [['framepact.analytics.visit.v1', JSON.stringify(saved)]] : []);
  const store = map => ({getItem:key=>map.get(key)||null,setItem:(key,value)=>map.set(key,value),removeItem:key=>map.delete(key)});
  const events = {}, scripts=[];
  const window = {dataLayer:[]};
  for (const [name,map] of [['localStorage',memory],['sessionStorage',session]]) {
    Object.defineProperty(window,name,{get(){if(blocked)throw new Error('storage denied');return store(map);}});
  }
  const document = {referrer:ref,head:{appendChild:s=>scripts.push(s)},createElement:()=>({}),
    addEventListener:(name,fn)=>(events[name] ||= []).push(fn)};
  const context = {window,document,location:{hostname:host,pathname:path,origin:'https://'+host,search},URL,URLSearchParams,Date};
  Object.defineProperty(context,'gtag',{get:()=>window.gtag});
  vm.runInNewContext(code,context);
  return {window,scripts,session,click(href){for(const fn of events.click||[])fn({target:{closest:s=>s==='a[href]'?{href}:null}});},
    calls(){return window.dataLayer.map(x=>Array.from(x));}};
}
test('internal and preview visits send nothing and load no Google tag',()=>{
  for(const args of [{exclude:true},{host:'preview.pages.dev'}]){
    const app=boot(args);app.click(FORM);assert.equal(app.calls().length,0);assert.equal(app.scripts.length,0);
  }
});
test('storage denial does not break bootstrap or contact clicks',()=>{
  const app=boot({blocked:true});app.click(FORM);assert.equal(app.calls().filter(x=>x[1]==='contact_form_click').length,1);
});
test('click is not submission, carries safe origin and page context',()=>{
  const app=boot({path:'/ai-video-price.html',ref:'https://chatgpt.com/c/private-conversation',search:'?email=secret@example.com'});
  app.click(FORM+'?usp=sf_link');
  const calls=app.calls(),clicks=calls.filter(x=>x[1]==='contact_form_click');
  assert.equal(clicks.length,1);assert.equal(clicks[0][2].observed_referrer,'chatgpt');
  assert.equal(clicks[0][2].contact_channel,'google_forms');
  assert.equal(calls.filter(x=>x[1]==='pricing_view').length,1);
  assert.equal(calls.filter(x=>x[1]==='generate_lead').length,0);
  assert.ok(!JSON.stringify(calls).includes('secret@example.com'));
  assert.ok(!JSON.stringify(calls).includes('private-conversation'));
});
test('session expiry resets landing information and self navigation preserves it',()=>{
  const old={landing:'/column.html',source:'google',lastSeen:Date.now()-31*60*1000};
  let app=boot({saved:old});app.click(FORM);assert.equal(app.calls().at(-1)[2].landing_page,'/');
  app=boot({saved:{...old,lastSeen:Date.now()},ref:'https://framepact.jp/column.html'});app.click(FORM);
  assert.equal(app.calls().at(-1)[2].landing_page,'/column.html');
});
test('unrelated links and forged storage do not leak values',()=>{
  const app=boot({saved:{lastSeen:Date.now(),landing:'/secret@example.com',source:'secret@example.com'}});
  app.click('https://example.com');assert.equal(app.calls().length,2);
  app.click(FORM);assert.ok(!JSON.stringify(app.calls()).includes('secret@example.com'));
});
test('every tracked public page uses one shared bootstrap and no legacy click emitter',()=>{
  let count=0;
  for(const name of fs.readdirSync('.').filter(n=>n.endsWith('.html'))){
    const text=fs.readFileSync(name,'utf8');
    assert.ok(!text.includes("gtag('config', 'G-HFRM2G8C7C')"),name);
    assert.ok(!text.includes('contact_form_click'),name);
    if(text.includes('/framepact-analytics.js')){count++;assert.equal(text.split('/framepact-analytics.js').length,2);}
  }
  assert.equal(count,21);
});
