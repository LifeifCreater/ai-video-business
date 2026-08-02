# FRAMEPACT

企業向けAI動画制作サービス「FRAMEPACT」の静的サイトです。

## Cloudflare Pages

- Build command: なし
- Build output directory: `/`（リポジトリルート）
- Production branch: `main`

`framepact.jp` は、Cloudflare Pages の **Custom domains** からプロジェクトへ関連付けてください。ルートの `CNAME` はCloudflare Pagesの設定を代替しません。

デプロイ前に、HTML内のローカル参照先、ページ内アンカー、HTML構文、25MiBの静的アセット上限を確認してください。

```sh
ruby scripts/check-site.rb
```
