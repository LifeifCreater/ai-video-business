#!/usr/bin/env python3
"""Local responsive regression; external media, analytics and forms are blocked.
Viewport cases cover fold/rotate/sidebar variations, not a certified device size.
--inline-fixture renders identical local assets in a network-disabled sandbox.
"""
import argparse, base64, functools, http.server, json, mimetypes, os, re, threading
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
PAGES=sorted(p for p in ROOT.glob('*.html') if p.name not in {'preview-home.html','analytics-owner.html'})
SIZES=[(320,568),(382,562),(390,664),(466,562),(466,678),(592,466),(626,730),(669,760),(768,600),(806,600),(867,648),(890,626),(951,669),(1024,768),(1280,800),(1440,900)]
CARD_COUNT=len(re.findall(r'class="article-card(?:\s|")', (ROOT/'column.html').read_text()))
OUT=Path(os.environ.get('RESPONSIVE_CHECK_OUTPUT','/tmp/framepact-responsive-check'))
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*_):pass

def fixture(path):
 from bs4 import BeautifulSoup
 dom=BeautifulSoup(path.read_text(),'html.parser')
 for el in dom.select('script[src],link[rel=stylesheet],img[src]'):
  attr='href' if el.name=='link' else 'src';url=el.get(attr,'');local=ROOT/urlsplit(url).path.lstrip('/')
  if url.startswith(('http:','https:','//')) or not local.is_file():continue
  if el.name=='script':el.attrs.pop('src');el.string=local.read_text()
  elif el.name=='link':
   style=dom.new_tag('style');style.string=local.read_text();el.replace_with(style)
  else:el['src']='data:'+(mimetypes.guess_type(local.name)[0] or 'application/octet-stream')+';base64,'+base64.b64encode(local.read_bytes()).decode()
 return str(dom)

LAYOUT="""() => ({overflow:document.documentElement.scrollWidth>innerWidth+1,
 hidden:[...document.querySelectorAll('.reveal')].filter(e=>+getComputedStyle(e).opacity<0.99).map(e=>e.className),
 clipped:[...document.querySelectorAll('main a,main button,main li,header a,footer a')].filter(e=>{
 const s=getComputedStyle(e),r=e.getBoundingClientRect();if(!r.width||!r.height||s.visibility==='hidden'||e.closest('[inert],.mobile-nav,table'))return false;
 return r.left < -2 || r.right > innerWidth+2;
 }).slice(0,5).map(e=>[e.tagName,e.className,e.textContent.trim().slice(0,60)])})"""
HIT="""e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
 return r.width>0&&r.height>0&&r.left>=-1&&r.right<=innerWidth+1&&r.top>=-1&&r.bottom<=innerHeight+1&&s.visibility!=='hidden'&&+s.opacity>.99&&h&&(e===h||e.contains(h));}"""

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','webkit'],default='chromium');parser.add_argument('--executable');parser.add_argument('--inline-fixture',action='store_true');parser.add_argument('--viewports',nargs='*');parser.add_argument('--layout-only',action='store_true');args=parser.parse_args();sizes=[tuple(map(int,x.split('x'))) for x in args.viewports] if args.viewports else SIZES
 OUT.mkdir(parents=True,exist_ok=True);shots=OUT/args.engine;shots.mkdir(exist_ok=True)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}'
 cache={p.name:fixture(p) for p in PAGES} if args.inline_fixture else {};failures=[];results=[]
 def check(ok,detail):
  if not ok:failures.append(detail)
 def load(page,name):
  if args.inline_fixture:page.set_content(cache[name],wait_until='domcontentloaded')
  else:page.goto(base+'/'+name,wait_until='load')
  page.evaluate("document.querySelectorAll('video').forEach(v=>v.pause())");page.evaluate("document.documentElement.style.setProperty('scroll-behavior','auto','important')");page.wait_for_timeout(35)
 def route(r):
  if not args.inline_fixture and r.request.url.startswith(base) and r.request.resource_type!='media':r.continue_()
  else:r.abort()
 try:
  with sync_playwright() as p:
   browser=getattr(p,args.engine).launch(**({'executable_path':args.executable} if args.executable else {}))
   for w,h in sizes:
    ctx=browser.new_context(viewport={'width':w,'height':h},has_touch=w<=1024,reduced_motion='no-preference');ctx.route('**/*',route)
    for file in PAGES:
     page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_default_timeout(5000);load(page,file.name)
     stats=page.evaluate(LAYOUT)
     for key in ['overflow','hidden','clipped']:check(not stats[key],[file.name,w,h,key,stats[key]])
     check(not errors,[file.name,w,h,'JS errors',errors])
     if file.name=='column.html':
      cards=page.locator('.article-card');check(cards.count()==CARD_COUNT and CARD_COUNT>0,[file.name,'card count changed'])
      check(page.locator('.article-card:not([hidden])').count()==min(6,CARD_COUNT),[file.name,'initial pagination'])
      if page.locator('#column-all').is_visible():page.locator('#column-all').click()
      for i in [0,cards.count()-1]:
       cards.nth(i).evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");check(cards.nth(i).evaluate(HIT),[file.name,w,h,i,'card unreachable'])
      cards.first.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})")
      if w in [390,466,669,867,951,1280]:page.screenshot(path=str(shots/f'column-{w}x{h}.png'))
     for table in page.locator('table').all():
      check(table.evaluate("""e=>{if(e.getBoundingClientRect().right<=innerWidth+1)return true;
       for(let a=e.parentElement;a;a=a.parentElement){if(['auto','scroll'].includes(getComputedStyle(a).overflowX)&&a.scrollWidth>a.clientWidth){a.scrollLeft=a.scrollWidth;const ok=a.scrollLeft>0;a.scrollLeft=0;return ok;}}return false;}"""),[file.name,w,h,'table clipped without scroll'])
     toggle=page.locator('#menuToggle')
     if not args.layout_only and w in [466,951] and toggle.count() and toggle.is_visible():
      page.evaluate("window.scrollTo({top:0,behavior:'instant'})");toggle.click();page.wait_for_timeout(400)
      check(toggle.get_attribute('aria-expanded')=='true',[file.name,w,'menu closed'])
      for a in page.locator('#mobileNav a').all():
       a.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");check(a.evaluate(HIT),[file.name,w,'menu link unreachable',a.inner_text()])
      page.keyboard.press('Escape');check(toggle.get_attribute('aria-expanded')=='false',[file.name,w,'menu failed to close'])
     results.append({'page':file.name,'size':[w,h],**stats});page.close()
    ctx.close();print(f'{args.engine}: {len(PAGES)} pages at {w}x{h}',flush=True)
   ctx=browser.new_context(viewport={'width':466,'height':562},has_touch=True,reduced_motion='reduce');ctx.route('**/*',route)
   for name in ([] if args.layout_only else ['column.html','index.html']):
    page=ctx.new_page();load(page,name)
    if name=='column.html' and page.locator('#column-all').is_visible():page.locator('#column-all').click()
    for w,h in [(466,562),(951,669),(669,951),(382,648),(592,466),(890,520),(466,678)]:
     page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(30)
     if name=='column.html':
      for a in page.locator('.article-card').all():a.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");check(a.evaluate(HIT),[name,w,h,'fold hid card'])
     else:
      check(page.locator('.contact-shortcut').evaluate(HIT),[name,w,h,'header contact inaccessible'])
      check(page.evaluate("()=>document.querySelector('main').getBoundingClientRect().bottom<=document.querySelector('.transport').getBoundingClientRect().top+1"),[name,w,h,'footer overlaps reading area'])
      for i in range(6):
       page.locator(f'.timeline [data-go="{i}"]').click()
       for a in page.locator('.scene.active').locator('a,button').all():
        a.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");check(a.evaluate(HIT),[name,w,h,i,'chapter link inaccessible',a.inner_text()])
      page.locator('.timeline [data-go="4"]').click();page.locator('[data-info="pricing"]').first.click()
      check(page.locator('#info-dialog .dialog-close').evaluate(HIT),[name,w,h,'dialog close clipped'])
      check(page.locator('#info-dialog').evaluate('e=>e.scrollWidth<=e.clientWidth+1'),[name,w,h,'dialog overflow'])
      page.keyboard.press('Escape')
      if w in [466,951]:page.screenshot(path=str(shots/f'home-{w}x{h}.png'))
    page.close()
   ctx.close()
   for mode in ['no-js','no-observer','observer-throws']:
    ctx=browser.new_context(viewport={'width':390,'height':664},java_script_enabled=mode!='no-js');ctx.route('**/*',route)
    init="delete window.IntersectionObserver;" if mode=='no-observer' else "window.IntersectionObserver=function(){throw new Error('simulated failure')};"
    if mode!='no-js':ctx.add_init_script(init)
    page=ctx.new_page()
    if args.inline_fixture and mode!='no-js':page.evaluate(init+';void 0;')
    load(page,'column.html');check(page.locator('.article-card').count()==CARD_COUNT and CARD_COUNT>0,[mode,'card count']);check(page.locator('.article-list').evaluate('e=>+getComputedStyle(e).opacity===1'),[mode,'list hidden']);ctx.close()
   browser.close()
 finally:server.shutdown();server.server_close()
 report={'engine':args.engine,'fixtureMode':args.inline_fixture,'pages':len(PAGES),'viewports':len(sizes),'pageViewportChecks':len(results),'failures':failures,'results':results}
 (OUT/f'{args.engine}-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 if failures:print(json.dumps(failures,ensure_ascii=False,indent=2));raise SystemExit(f'{len(failures)} responsive assertions failed')
 print(f'{len(results)} page/viewport checks plus reflow, menus, tables, dialogs and visibility fallbacks passed. No forms submitted.')
if __name__=='__main__':main()
