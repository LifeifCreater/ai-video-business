# 初回dry-run結果

- 実施日: 2026-08-04 JST
- sitemap: `https://framepact.jp/sitemap.xml`
- ローカルsitemap URL数: 15
- 重複URL: 0
- lastmod欠落: 0
- 初期台帳登録: 15
- Search Consoleプロパティ候補: `https://framepact.jp/`
- API認証: 未実施（Secret未設定。成功扱いにしない）
- sitemap送信: 本番deployment成功確認後。dry-runでは未送信
- URL Inspection: 公開日を確認できる4記事は2026-08-05 08:30 JST以降。公開日不明の既存11 URLは公開日の確認が必要
- 朝会連携: JSON形式と最大5件ルールを実装。API値は未取得のためnull

コードと台帳は実行可能。実API稼働にはGoogle Cloud設定、Search Console権限、GitHub Secret、Cloudflare deployment status連携の確認が必要。
