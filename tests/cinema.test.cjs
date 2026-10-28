'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('framepact-cinema.js', 'utf8');

// Execute the production routing/dialog functions with a minimal event fixture.
// This is a behavior test, not a replacement for browser layout/focus checks.
function boot(hash='') {
  const emitted=[], opened=[], scenes=[];
  const nodes={'info-title':{},'info-content':{}};
  const button={dataset:{info:'pricing'},addEventListener(name,fn){this[name]=fn;}};
  const context={
    document:{getElementById:id=>nodes[id],dispatchEvent:event=>emitted.push(event.type),querySelectorAll:()=>[button]},
    Event:class {constructor(type){this.type=type;}},
    location:{hash}, info:{scrollTop:25},
    infoCopy:{pricing:['Pricing','safe pricing content'],faq:['FAQ','safe FAQ content']},
    ids:['opening','possibilities','works','human','process','contact'],
    openDialog:dialog=>opened.push(dialog),showScene:(n,update)=>scenes.push([n,update]),
  };
  vm.createContext(context);
  for(const prefix of ['function showInfo(',"document.querySelectorAll('[data-info]')",'function routeHash(']){
    const line=source.split('\n').find(line=>line.startsWith(prefix));
    assert.ok(line,`production code not found: ${prefix}`);
    vm.runInContext(line,context);
  }
  return {context,emitted,opened,nodes,button,scenes,route(){vm.runInContext('routeHash()',context);}};
}
test('pricing deep link and subsequent hash navigation notify once per actual opening',()=>{
  const app=boot('#price');app.route();
  assert.deepEqual(app.emitted,['framepact:pricing-view']);
  assert.deepEqual(app.scenes,[[4,false]]);
  assert.equal(app.nodes['info-title'].textContent,'Pricing');
  assert.equal(app.context.info.scrollTop,0);
  app.context.location.hash='#faq';app.route();
  assert.equal(app.emitted.length,1);
  app.context.location.hash='#price';app.route();
  assert.equal(app.emitted.length,2);
});
test('pricing button shares the same actual-open notification and unrelated routes do not emit',()=>{
  const app=boot('#contact');app.route();
  assert.equal(app.emitted.length,0);
  app.button.click();
  assert.deepEqual(app.emitted,['framepact:pricing-view']);
  assert.equal(app.opened.length,1);
});

function keyboardFixture({sceneOverflow=false,mainOverflow=false}={}){
  const scrolls=[],navigations=[];
  const node=(name,overflow)=>({clientHeight:300,scrollHeight:overflow?600:300,
    scrollTo:options=>scrolls.push([name,'to',options.top]),scrollBy:options=>scrolls.push([name,'by',options.top])});
  const scene=node('scene',sceneOverflow),main=node('main',mainOverflow);
  let handler;
  const context={scenes:[scene],current:0,dialogs:[],cinema:{querySelector:()=>main},
    window:{addEventListener:(name,fn)=>{if(name==='keydown')handler=fn;}},showScene:n=>navigations.push(n)};
  vm.createContext(context);
  vm.runInContext(source.slice(source.indexOf('function chapterScrollTarget()'),source.indexOf('// A deliberate wheel')),context);
  return {scrolls,navigations,key(key,target={tagName:'BUTTON'}){
    let prevented=false;handler({key,target,preventDefault(){prevented=true;}});return prevented;
  }};
}
test('overflow keyboard controls scroll the chapter even when focus is in navigation',()=>{
  const app=keyboardFixture({sceneOverflow:true});
  for(const key of ['PageDown','PageUp','Home','End'])assert.equal(app.key(key),true);
  assert.deepEqual(app.scrolls,[['scene','by',240],['scene','by',-240],['scene','to',0],['scene','to',600]]);
  assert.deepEqual(app.navigations,[]);
});
test('short-view main scrolling and editing targets are preserved',()=>{
  const app=keyboardFixture({mainOverflow:true});
  app.key('PageDown');assert.deepEqual(app.scrolls,[['main','by',240]]);
  assert.equal(app.key('End',{tagName:'INPUT'}),false);
  assert.equal(app.key('End',{tagName:'DIV',isContentEditable:true}),false);
  assert.equal(app.scrolls.length,1);
  const normal=keyboardFixture();normal.key('PageDown');assert.deepEqual(normal.navigations,[1]);
});
