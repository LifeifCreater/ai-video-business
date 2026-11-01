const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('framepact-analytics.js', 'utf8');
const FORM = 'https://docs.google.com/forms/d/e/1FAIpQLSeS-G-8U9p5-zMiFGaH3Y0TZjswVbvKOLl1Rg1_uK2GKw0blg/viewform';
const MV_PORTFOLIO_IDS = ['mv-1','mv-2','mv-3'];
const PORTFOLIO_IDS = [...MV_PORTFOLIO_IDS,'showreel','brand-pr','training'];
const PORTFOLIO_PLACEMENTS = ['homepage_card','homepage_dialog','portfolio_case','portfolio_intro','portfolio_footer','service_related'];
function boot({host='framepact.jp', path='/', exclude=false, blocked=false, saved=null, ref='', search='', hash=''}={}) {
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
  const context = {window,document,location:{hostname:host,pathname:path,origin:'https://'+host,search,hash},URL,URLSearchParams,Date};
  Object.defineProperty(context,'gtag',{get:()=>window.gtag});
  vm.runInNewContext(code,context);
  return {window,scripts,session,click(href,dataset={}){for(const fn of events.click||[])fn({target:{closest:s=>s==='a[href]'?{href,dataset}:null}});},
    dispatch(name,detail){for(const fn of events[name]||[])fn({type:name,detail});},
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
test('public marketing pages use one shared bootstrap and preserve untracked utility pages',()=>{
  const pages=fs.readdirSync('.').filter(n=>n.endsWith('.html'));
  // Existing legal disclosure, error and analytics-control pages are intentionally untracked.
  const untracked=new Set(['operator.html','404.html','analytics-owner.html']);
  assert.ok(pages.length>0);
  for(const name of pages){
    const text=fs.readFileSync(name,'utf8');
    assert.ok(!text.includes("gtag('config', 'G-HFRM2G8C7C')"),name);
    assert.ok(!text.includes('contact_form_click'),name);
    const bootstrapCount=text.split('/framepact-analytics.js').length-1;
    const indexable=name!=='404.html'&&!/<meta\s+name="robots"\s+content="noindex/i.test(text);
    if(untracked.has(name))assert.equal(bootstrapCount,0,`${name}: preserve untracked utility page`);
    else if(indexable)assert.equal(bootstrapCount,1,`${name}: shared analytics bootstrap`);
    else assert.ok(bootstrapCount<=1,`${name}: duplicated analytics bootstrap`);
  }
});

test('actual pricing dialog openings count once without generating leads',()=>{
  const app=boot();
  app.dispatch('framepact:pricing-view');
  assert.equal(app.calls().filter(x=>x[1]==='pricing_view').length,1);
  app.dispatch('framepact:pricing-view');
  assert.equal(app.calls().filter(x=>x[1]==='pricing_view').length,2);
  assert.equal(app.calls().filter(x=>x[1]==='generate_lead').length,0);
  for(const args of [{exclude:true},{host:'preview.pages.dev'}]){
    const excluded=boot(args);excluded.dispatch('framepact:pricing-view');
    assert.equal(excluded.calls().length,0);
  }
});

test('portfolio consultation clicks preserve the selected work without counting a submission',()=>{
  const app=boot({path:'/mv-portfolio.html'});
  for(const portfolioId of PORTFOLIO_IDS){
    for(const ctaLocation of PORTFOLIO_PLACEMENTS){
      app.click(FORM,{portfolioId,ctaLocation});
      const event=app.calls().filter(call=>call[1]==='contact_form_click').at(-1);
      assert.equal(event[2].portfolio_id,portfolioId);
      assert.equal(event[2].cta_location,ctaLocation);
      assert.equal(event[2].contact_channel,'google_forms');
    }
  }
  assert.equal(app.calls().filter(call=>call[1]==='contact_form_click').length,PORTFOLIO_IDS.length*PORTFOLIO_PLACEMENTS.length);
  assert.equal(app.calls().filter(call=>call[1]==='generate_lead').length,0);
});

test('portfolio events describe deliberate actions and never imply completed playback',()=>{
  const app=boot({path:'/mv-portfolio.html',hash:'#mv-3'});
  const views=app.calls().filter(call=>call[1]==='portfolio_view');
  assert.equal(views.length,1);
  assert.equal(views[0][2].portfolio_id,'mv-3');
  for(const portfolio_id of PORTFOLIO_IDS){
    for(const action of ['video_open','video_external','copy_brief']){
      for(const placement of PORTFOLIO_PLACEMENTS){
        app.dispatch('framepact:portfolio-action',{portfolio_id,action,placement});
        const event=app.calls().at(-1);
        assert.equal(event[1],'portfolio_'+action);
        assert.equal(event[2].portfolio_id,portfolio_id);
        assert.equal(event[2].cta_location,placement);
      }
    }
  }
  const names=app.calls().filter(call=>call[0]==='event').map(call=>call[1]);
  assert.equal(names.length,1+PORTFOLIO_IDS.length*3*PORTFOLIO_PLACEMENTS.length);
  assert.ok(!names.some(name=>['generate_lead','video_start','video_complete'].includes(name)));
});

test('portfolio page views associate only the three existing MV anchors',()=>{
  for(const id of [...PORTFOLIO_IDS,'mv-4','private@example.com']){
    const app=boot({path:'/mv-portfolio.html',hash:'#'+id});
    const views=app.calls().filter(call=>call[1]==='portfolio_view');
    assert.equal(views.length,1);
    assert.equal(views[0][2].portfolio_id,MV_PORTFOLIO_IDS.includes(id)?id:undefined);
    assert.equal(views[0][2].page_location,'https://framepact.jp/mv-portfolio.html');
    assert.ok(!JSON.stringify(app.calls()).includes('private@example.com'));
  }
});

test('arbitrary portfolio metadata and malformed custom events cannot leak personal data',()=>{
  const marker='private@example.com';
  const app=boot({path:'/mv-portfolio.html',search:'?portfolio_id='+marker});
  for(const data of [
    {portfolioId:marker,ctaLocation:marker},
    {portfolioId:'mv-4',ctaLocation:'homepage_dialog'},
    {portfolioId:'showreel',ctaLocation:marker}]){
    app.click(FORM,data);
    const click=app.calls().filter(call=>call[1]==='contact_form_click').at(-1);
    assert.equal(click[2].portfolio_id,undefined);
    assert.equal(click[2].cta_location,undefined);
  }
  const count=app.calls().length;
  for(const detail of [undefined,null,{},
    {portfolio_id:marker,action:'video_open',placement:'portfolio_case'},
    {portfolio_id:'mv-4',action:'video_open',placement:'portfolio_case'},
    {portfolio_id:'mv-1',action:marker,placement:'portfolio_case'}]){
    app.dispatch('framepact:portfolio-action',detail);
  }
  assert.equal(app.calls().length,count,'invalid identities and actions are ignored');
  app.dispatch('framepact:portfolio-action',{portfolio_id:'mv-1',action:'video_open',placement:marker,email:marker});
  assert.equal(app.calls().length,count,'unknown placements are ignored');
  for(const portfolio_id of ['showreel','brand-pr','training']){
    app.dispatch('framepact:portfolio-action',{portfolio_id,action:'copy_brief',placement:'homepage_dialog',email:marker,brief:marker});
    assert.equal(app.calls().at(-1)[2].portfolio_id,portfolio_id);
  }
  assert.ok(!JSON.stringify(app.calls()).includes(marker));
});

test('portfolio page and actions respect internal and preview analytics exclusion',()=>{
  for(const args of [{exclude:true},{host:'preview.pages.dev'}]){
    const app=boot({...args,path:'/mv-portfolio.html'});
    for(const portfolioId of PORTFOLIO_IDS){
      app.click(FORM,{portfolioId,ctaLocation:'portfolio_case'});
      app.dispatch('framepact:portfolio-action',{portfolio_id:portfolioId,action:'video_open',placement:'portfolio_case'});
    }
    assert.equal(app.calls().length,0);
    assert.equal(app.scripts.length,0);
  }
});

