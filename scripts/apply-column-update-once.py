#!/usr/bin/env python3
"""One-shot owner-authorized publication and navigation update; no posts or analytics changes."""
import hashlib, html, json, re, subprocess
from pathlib import Path
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
ROOT=Path.cwd()
DATE='2026-10-31'
SOURCES=[
 ('WR-20261025-001','writing/inbox/WR-20261025-001-video-speed-change-approval-check.md','training-video-playback-speed-checklist.html','研修・マニュアル','training','2026-10-25'),
 ('WR-20261025-002','writing/inbox/WR-20261025-002-source-audio-extraction-governance.md','video-audio-track-extraction-checklist.html','音声・映像編集','materials','2026-10-25'),
 ('WR-20260927-003','writing/review/WR-20260927-003-document-to-video-summary-governance-reviewed.md','document-to-video-summary-governance.html','研修・マニュアル','training','2026-10-09'),
 ('WR-20260920-001','writing/review/WR-20260920-001-training-video-structure-reviewed.md','training-video-structure.html','研修・マニュアル','training','2026-10-08'),
 ('WR-20260927-002','writing/review/WR-20260927-002-published-video-replacement-rollback-reviewed.md','published-video-replacement-rollback.html','公開・更新管理','operations','2026-10-07'),
]
def read(name):return (ROOT/name).read_text()
def write(name,text):
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
def esc(s):return html.escape(s,quote=True)
# Remove note links from rendered pages AND their shared generator template.
removed=0
for p in [*ROOT.glob('*.html'),ROOT/'templates/article-social.html']:
 text=p.read_text();original=text
 text,n=re.subn(r'<li>\s*<a\b[^>]*href=["\']https?://(?:www\.)?note\.com[^"\']*["\'][^>]*>.*?</a>\s*</li>\s*','',text,flags=re.S);removed+=n
 text,n=re.subn(r'<a\b[^>]*href=["\']https?://(?:www\.)?note\.com[^"\']*["\'][^>]*>.*?</a>','',text,flags=re.S);removed+=n
 text=re.sub(r'<link\b[^>]*href=["\']https?://(?:www\.)?note\.com[^"\']*["\'][^>]*>\s*','',text)
 # Remove the now-unwanted profile reference from structured data, not other accounts.
 text=re.sub(r',\s*"https://note\.com/framepact"','',text)
 text=re.sub(r'"https://note\.com/framepact"\s*,','',text)
 if text!=original:p.write_text(text)
subprocess.run(['python3','scripts/sync-article-social.py'],check=True)
# Maintain the existing production assertion, reversing only the removed note link requirement.
p='.github/workflows/production-smoke-check.yml'
s=read(p);old="          grep -q 'https://note.com/framepact' /tmp/home.html"
assert old in s
s=s.replace(old,"          if grep -Eq 'https?://(www\\.)?note\\.com' /tmp/home.html; then echo 'Unexpected note link'; exit 1; fi")
write(p,s)
# Reuse the existing page shell, contact CTA and visual language. Only the public manuscript body is rendered.
template=read('corporate-pr-video-storyboard.html')
old_dom=BeautifulSoup(template,'html.parser')
contact=str(old_dom.select_one('#contact'))
md=MarkdownIt('commonmark',{'html':False}).enable('table')
articles=[]
for wid,source,slug,label,category,created in SOURCES:
 text=read(source);title=text.splitlines()[0].removeprefix('# ').strip()
 description=re.search(r'## description(?:案)?\s*\n+([^\n]+)',text).group(1).strip()
 body=text.split('\n---\n',1)[1].split('\n---\n\n## 編集管理メモ',1)[0].strip()
 assert all(x not in body for x in ['## 原稿管理情報','## 編集管理メモ','## title案'])
 content=BeautifulSoup(md.render(body),'html.parser')
 headings=[]
 for i,h in enumerate(content.select('h2'),1):h['id']=f'section-{i}';headings.append((h['id'],h.get_text()))
 for i,t in enumerate(content.select('table'),1):
  wrapper=content.new_tag('div',attrs={'class':'table-wrap','role':'region','aria-label':f'確認表{i}（横にスクロールできます）','tabindex':'0'})
  t.wrap(wrapper)
 url='https://framepact.jp/'+slug
 dom=BeautifulSoup(template,'html.parser');dom.body['class']=['column-article']
 dom.title.string=title+'｜Framepact'
 for selector,value in [('meta[name=description]',description),('meta[property="og:title"]',title+'｜Framepact'),('meta[property="og:description"]',description),('meta[property="og:url"]',url),('meta[property="og:image:alt"]',title),('meta[name="twitter:title"]',title+'｜Framepact'),('meta[name="twitter:description"]',description)]:dom.select_one(selector)['content']=value
 dom.select_one('link[rel=canonical]')['href']=url
 schema=json.loads(dom.select_one('script[type="application/ld+json"]').string)
 for node in schema['@graph']:
  typ=node['@type']
  if typ=='WebPage':node.update({'@id':url+'#webpage','url':url,'name':title+'｜Framepact','description':description})
  if typ=='BreadcrumbList':
   node['@id']=url+'#breadcrumb';node['itemListElement'][-1].update(name=title,item=url)
  if typ=='Article':node.update({'@id':url+'#article','headline':title,'description':description,'datePublished':DATE,'dateModified':DATE,'mainEntityOfPage':{'@id':url+'#webpage'}})
 dom.select_one('script[type="application/ld+json"]').string='\n'+json.dumps(schema,ensure_ascii=False,indent=2)+'\n'
 css=dom.new_tag('link',rel='stylesheet',href='/framepact-column.css?v=20261031');dom.head.append(css)
 related=[('/column.html','お役立ち記事一覧','企画・発注から映像編集まで、関連記事を探す。'),('/training-video.html' if category=='training' else '/event-video.html' if wid.endswith('1025-002') else '/corporate-pr-video.html','目的に合わせた動画制作を相談する','用途・素材・確認体制から制作範囲を整理します。')]
 if wid=='WR-20261025-002':related.append(('/ai-audio-processing-approval.html','AI音声処理の承認基準','AIによるノイズ低減・話者分離を扱う既存記事。'))
 else:related.append(('/video-production-brief-template.html','動画制作の依頼書テンプレート','見積もり前に制作条件を整理する。'))
 toc='<details class="article-toc"><summary>目次（'+str(len(headings))+'項目）</summary><ol>'+''.join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i,t in headings)+'</ol></details>'
 rel='<section class="section section--offwhite" id="related-services"><div class="wrap"><h2 class="h2">あわせて読みたい</h2><div class="related-grid">'+''.join(f'<a class="related-card" href="{p}"><span class="related-card-title">{esc(t)}<span class="related-card-arrow" aria-hidden="true">→</span></span><span class="related-card-desc">{esc(d)}</span></a>' for p,t,d in related)+'</div></div></section>'
 main=f'''<main><section class="page-hero"><div class="page-hero-grid" aria-hidden="true"></div><div class="wrap"><nav class="breadcrumb" aria-label="パンくずリスト"><a href="/">ホーム</a><span aria-hidden="true">/</span><a href="/column.html">お役立ち記事</a></nav><div class="page-hero-inner"><span class="page-hero-tag">{esc(label)}</span><h1 class="page-hero-title">{esc(title)}</h1><p class="page-hero-sub">{esc(description)}</p><p class="article-meta">公開日：<time datetime="{DATE}">2026年10月31日</time></p></div></div></section><article class="section article-reading"><div class="wrap">{toc}<div class="body-copy">{content}</div></div></article>{rel}{contact}</main>'''
 dom.main.replace_with(BeautifulSoup(main,'html.parser').main)
 output=str(dom).replace('<meta content="width=device-width, initial-scale=1.0" name="viewport"/>','<meta name="viewport" content="width=device-width, initial-scale=1.0">');assert output.startswith('<!DOCTYPE html>')
 write(slug,output+'\n')
 articles.append({'id':wid,'source':source,'url':'/'+slug,'title':title,'description':description,'category':category,'categoryLabel':label,'createdAt':created,'publishedAt':DATE})
 # Record this explicit publication authorization without retroactively changing past review records.
 text=re.sub(r'^- ステータス:.*$', '- ステータス: 公開実装承認済み（2026-10-31、オーナー）／公開用HTML実装済み',text,flags=re.M)
 text=re.sub(r'^- 公開承認:.*$', '- 公開承認: 承認済み（2026-10-31、未掲載完成記事の全反映・マージ指示）',text,flags=re.M)
 text=text.replace('（仮、未実装）','（公開用HTML実装済み）')
 text=text.replace('承認までは現在のパスを維持する','公開後も出典追跡用に現在のパスを維持する')
 text+='\n## 2026-10-31 公開実装記録（内部管理）\n\n- オーナーの未掲載完成記事の全反映・マージ指示に基づき実装。過去のマージを公開承認へ読み替えたものではない。\n- 公開先: '+url+'\n- 公開日表示: 2026-10-31（原稿作成日を遡及使用しない）\n- 承認・実装範囲: [リリース記録](../releases/RELEASE-20261031-columns.md)\n- 本番反映の成否: マージ後のProduction smoke checkで確認。原稿・記事本文からは本管理情報を除外。\n'
 write(source,text)
# Add all five newest articles to the index, preserving the existing thirteen cards and dates.
s=read('column.html');dom=BeautifulSoup(s,'html.parser');old_cards=dom.select('.article-card')
assert len(old_cards)==13
cats={
 'corporate-pr-video-storyboard.html':'planning','video-production-brief-template.html':'planning','video-production-company-vs-ai-creator.html':'planning','ai-generated-insert-shot-register.html':'materials','ai-audio-processing-approval.html':'materials','youtube-shorts-thumbnail-approval.html':'operations','ai-avatar-training-video-operations.html':'training','ai-video-ad-disclosure.html':'operations','ai-video-data-management.html':'materials','multi-platform-video-production.html':'operations','ai-video-outsourcing-checklist.html':'planning','ai-video-vs-traditional-video.html':'planning','what-is-ai-video-production.html':'planning'}
new_cards=[]
for a in articles:
 new_cards.append(f'<a class="article-card" data-category="{a["category"]}" href="{a["url"]}"><span class="article-card-category">{esc(a["categoryLabel"])}</span><span class="article-card-title">{esc(a["title"])}</span><span class="article-card-desc">{esc(a["description"])}</span><span class="article-card-meta"><time datetime="{DATE}">2026年10月31日</time><span class="article-card-arrow" aria-hidden="true">読む →</span></span></a>')
for card in old_cards:
 card['data-category']=cats[card['href'].lstrip('/')];card.select_one('.article-card-arrow').string='読む →';new_cards.append(str(card))
card_html='\n'.join(new_cards)
controls='''<div class="column-tools" data-column-controls hidden><label for="column-search">キーワードで探す<input type="search" id="column-search" placeholder="例：研修、料金、音声" maxlength="100" autocomplete="off" aria-controls="column-cards"></label><label for="column-category">テーマ<select id="column-category" aria-controls="column-cards"><option value="">すべて</option><option value="training">研修・マニュアル</option><option value="planning">企画・発注</option><option value="materials">AI・素材・音声</option><option value="operations">公開・運用</option></select></label><button class="column-reset" id="column-reset" type="button">条件をクリア</button></div>'''
section=f'''<section class="section" id="article-list"><div class="wrap"><div class="section-head"><h2 class="h2">記事を探す</h2><p class="column-status" id="column-status" role="status" aria-live="polite" aria-atomic="true">全18記事｜新しい順</p></div>{controls}<div class="article-list" id="column-cards">{card_html}</div><p class="column-empty" id="column-empty" hidden>一致する記事がありません。キーワードやテーマを変えてお試しください。</p><div class="column-more" data-column-more hidden><button type="button" id="column-next" aria-controls="column-cards">さらに6件を見る</button><button type="button" id="column-all" aria-controls="column-cards">すべて表示</button></div><noscript><p class="article-list-note">すべての記事を表示しています。</p></noscript></div></section>'''
# Replace only the relevant section so existing header, footer, menu JS and SEO remain intact.
start=s.index('  <section class="section" id="article-list">');end=s.index('</section>',start)+len('</section>')
s=s[:start]+section+s[end:]
s=s.replace('<body>','<body class="column-index">',1)
s=s.replace('</head>','<link rel="stylesheet" href="/framepact-column.css?v=20261031">\n<script src="/framepact-column.js?v=20261031" defer></script>\n</head>',1)
s=s.replace('AI動画制作、企業動画、料金、活用方法、注意点など、企業担当者に向けた情報を発信しています。','企画・料金・AI活用の疑問を、記事で解決。')
write('column.html',s)
# Reverse links from related services / existing audio article.
for name,ids in [('training-video.html',[0,2,3]),('event-video.html',[1]),('corporate-pr-video.html',[4]),('ai-audio-processing-approval.html',[1])]:
 s=read(name);marker=re.search(r'<div class="related-grid(?: reveal)?">',s);assert marker,name
 links=''.join(f'<a class="related-card" href="{articles[i]["url"]}"><span class="related-card-title">{esc(articles[i]["title"])}<span class="related-card-arrow" aria-hidden="true">→</span></span><span class="related-card-desc">{esc(articles[i]["description"])}</span></a>' for i in ids)
 s=s[:marker.end()]+links+s[marker.end():];write(name,s)
# Include pages in sitemap with their real first publication date.
s=read('sitemap.xml');assert s.count('</urlset>')==1
s=s.replace('</urlset>',''.join(f'  <url><loc>https://framepact.jp{a["url"]}</loc><lastmod>{DATE}</lastmod></url>\n' for a in articles)+'</urlset>')
write('sitemap.xml',s)
# Persistent, scoped release record; do not mutate X/note queues or unrelated stale approval jobs.
write('writing/releases/RELEASE-20261031-columns.md','# 2026-10-31 コラム公開実装\n\nオーナーの「10/3以降の未掲載記事を全て反映」「noteへの誘導を全て削除」「全てマージまで」の依頼に基づく。対象はレビュー済み完成原稿5本。企画だけの項目や他媒体の原稿は対象外。\n\n| 原稿ID | 原稿作成日 | 公開日表示 | 公開先 |\n|---|---|---|---|\n'+''.join(f'| {a["id"]} | {a["createdAt"]} | {DATE} | https://framepact.jp{a["url"]} |\n' for a in articles)+'\n原稿本文は既存のレビュー済み正本から変換。管理情報・内部メモは公開本文から除外。タイトル・description・canonical・Article構造化データ・目次・横スクロール表・サービスへのリンク・逆リンク・記事一覧・sitemapを実装。Google Vidsの公式発表は2026-10-31に再確認（速度記事のモバイルURLと音声抽出記事）。ヘルプの確認日は既存の2026-10-30を維持。実機動作・問い合わせ送信は未試験。\n\n公開用HTML実装と本番反映を区別する。本番公開の成否は本PRマージ後のCloudflare buildとProduction smoke checkを正本とする。日付は原稿作成日に遡らせない。X/note投稿・予約・キューや契約・計測設定は変更しない。\n')
write('writing/releases/columns-20261031.json',json.dumps({'date':DATE,'approval':'2026-10-31 owner instruction to publish all completed unlisted articles and merge','articles':articles},ensure_ascii=False,indent=2)+'\n')
# Existing responsive tests should inspect default pagination then deliberately reveal all cards.
p='scripts/check-responsive-browser.py';s=read(p)
s=s.replace("cards=page.locator('.article-card');check(cards.count()==CARD_COUNT and CARD_COUNT>0,[file.name,'card count changed'])", "cards=page.locator('.article-card');check(cards.count()==CARD_COUNT and CARD_COUNT>0,[file.name,'card count changed'])\n      check(page.locator('.article-card:not([hidden])').count()==min(6,CARD_COUNT),[file.name,'initial pagination'])\n      if page.locator('#column-all').is_visible():page.locator('#column-all').click()")
s=s.replace("page=ctx.new_page();load(page,name)\n    for w,h", "page=ctx.new_page();load(page,name)\n    if name=='column.html' and page.locator('#column-all').is_visible():page.locator('#column-all').click()\n    for w,h")
write(p,s)
p='.github/workflows/responsive-validation.yml';s=read(p).replace("      - 'framepact-cinema.js'","      - 'framepact-*.js'").replace("      - 'tests/responsive.test.cjs'","      - 'tests/responsive.test.cjs'\n      - 'scripts/check-column-browser.py'")
s=s.replace('          python scripts/check-responsive-browser.py --engine "$ENGINE" --viewports $sizes','          python scripts/check-responsive-browser.py --engine "$ENGINE" --viewports $sizes\n          python scripts/check-column-browser.py --engine "$ENGINE"')
write(p,s)
subprocess.run(['python3','scripts/sync-article-social.py'],check=True)
print('Published HTML for',len(articles),'manuscripts; index now contains 18 articles; note anchors removed:',removed)

p='tests/analytics.test.cjs';s=read(p);assert 'assert.equal(count,26);' in s;write(p,s.replace('assert.equal(count,26);','assert.equal(count,31);'))
p='writing/writing-register.md';s=read(p)
for a in articles:
 assert '`'+a['id']+'`' not in s
 plan=a['id'].replace('WR-','PLAN-')
 s+=f"| `{a['id']}` | `{plan}` | {a['title']} | コラム | 企業の制作発注担当者 | {a['createdAt']} | コンテンツライター担当 | `公開用HTML実装済み・反映確認はリリースPR参照` | 既存レビュー参照 | `合格` | `合格` | {'2026-10-30' if a['id'].startswith('WR-20261025') else a['createdAt']} | `本文変更時` | `原稿・公開実装・マージ承認済み（2026-10-31、オーナー）` | 2026-10-31 |  | `{a['source']}` | 公開先 https://framepact.jp{a['url']} 。releases/RELEASE-20261031-columns.md参照。X/note対象外 |\n"
write(p,s)
p='sitemap.xml';s=read(p)
for route in ['/','/column.html','/training-video.html','/event-video.html','/corporate-pr-video.html','/ai-audio-processing-approval.html']:
 pattern=r'(<loc>https://framepact\.jp'+re.escape(route)+r'</loc>\s*<lastmod>)[^<]+(</lastmod>)'
 s,n=re.subn(pattern,r'\g<1>2026-10-31\2',s);assert n==1,(route,n)
write(p,s)
p='tests/seo.test.cjs';s=read(p);old="const lastmod = page === 'index.html' ? '2026-10-29' : '2026-10-25';";assert old in s
write(p,s.replace(old,"const lastmod = ['index.html','training-video.html','event-video.html','corporate-pr-video.html'].includes(page) ? '2026-10-31' : '2026-10-25';"))
p='_redirects';s=read(p);assert '/note https://note.com/framepact 302' in s
s=s.replace('/note https://note.com/framepact 302','/note /column.html 302')
s+='\n# Reviewed columns published 2026-10-31.\n'
for a in articles:
 stem=a['url'][:-5]
 for alias in [stem,stem+'/',stem+'/index.html']:s+=f"{alias} {a['url']} 301\n"
write(p,s)
