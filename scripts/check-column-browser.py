#!/usr/bin/env python3
"""Read-only local index usability tests. Never contact analytics or submit forms."""
import argparse,functools,http.server,importlib.util,json,os,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('RESPONSIVE_CHECK_OUTPUT','/tmp/framepact-responsive-check'))
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*_):pass

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--engine',default='chromium',choices=['chromium','webkit']);parser.add_argument('--executable');parser.add_argument('--inline-fixture',action='store_true');args=parser.parse_args()
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}'
 spec=importlib.util.spec_from_file_location('responsive',ROOT/'scripts/check-responsive-browser.py');responsive=importlib.util.module_from_spec(spec);spec.loader.exec_module(responsive)
 output=OUT/args.engine;output.mkdir(parents=True,exist_ok=True);stats=[]
 def route(r):
  if not args.inline_fixture and r.request.url.startswith(base) and r.request.resource_type!='media':r.continue_()
  else:r.abort()
 def load(p):
  if args.inline_fixture:p.set_content(responsive.fixture(ROOT/'column.html'),wait_until='load')
  else:p.goto(base+'/column.html',wait_until='load')
  p.wait_for_timeout(100)
 try:
  with sync_playwright() as pw:
   browser=getattr(pw,args.engine).launch(**({'executable_path':args.executable} if args.executable else {}))
   for w,h in [(320,568),(390,664),(466,562),(669,760),(951,669),(1280,800)]:
    ctx=browser.new_context(viewport={'width':w,'height':h},has_touch=True);ctx.route('**/*',route);p=ctx.new_page();load(p)
    cards=p.locator('.article-card');visible=p.locator('.article-card:not([hidden])');assert cards.count()==18;assert visible.count()==6
    assert p.locator('.article-card time').first.get_attribute('datetime')=='2026-10-31'
    assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    assert p.locator('a[href*="note.com"]').count()==0
    first=cards.first;first.scroll_into_view_if_needed();assert first.evaluate(responsive.HIT)
    height=first.bounding_box()['height'];assert w>600 or height<=240,(w,height)
    p.screenshot(path=str(output/f'column-compact-{w}x{h}.png'))
    p.locator('#column-next').click();assert visible.count()==12
    p.locator('#column-all').click();assert visible.count()==18;assert not p.locator('[data-column-more]').is_visible()
    p.locator('#column-category').select_option('training');assert visible.count()==4
    p.locator('#column-search').fill('マニュアル');assert visible.count()>0
    p.locator('#column-search').fill('存在しない検索語999');assert visible.count()==0;assert p.locator('#column-empty').is_visible()
    p.locator('#column-reset').click();assert visible.count()==6;assert p.locator('#column-search').evaluate('e=>e===document.activeElement')
    p.locator('#column-search').fill('音声');assert visible.count()==3
    if not args.inline_fixture:
     p.reload(wait_until='load');assert p.locator('#column-search').input_value()=='音声';assert visible.count()==3
    p.locator('#column-reset').click();p.locator('#column-all').click()
    for a in cards.all():a.scroll_into_view_if_needed();assert a.evaluate(responsive.HIT)
    stats.append({'width':w,'height':h,'firstCardHeight':height,'articles':18,'initialVisible':6});ctx.close()
   ctx=browser.new_context(viewport={'width':390,'height':664},java_script_enabled=False);ctx.route('**/*',route);p=ctx.new_page();load(p);assert p.locator('.article-card:not([hidden])').count()==18;assert not p.locator('[data-column-controls]').is_visible();ctx.close()
   browser.close()
 finally:server.shutdown();server.server_close()
 (output/'column-compact-results.json').write_text(json.dumps({'engine':args.engine,'fixture':args.inline_fixture,'results':stats,'success':True},ensure_ascii=False,indent=2))
 print('Column: compact cards, 6/12/18 pagination, filters, empty state, reset, URL restore and no-JS fallback passed.')
if __name__=='__main__':main()
