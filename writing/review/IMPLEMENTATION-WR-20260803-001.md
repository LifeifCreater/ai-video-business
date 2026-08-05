# 公開実装計画: WR-20260803-001

## 管理情報

- 原稿ID: `WR-20260803-001`
- 承認済み原稿: `writing/approved/WR-20260803-001-ai-video-outsourcing-checklist.md`
- 計画作成日: `2026-08-03`
- 原稿承認: `承認済み（2026-08-03、オーナー）`
- 公開実装承認: `承認済み（2026-08-03、オーナー）`
- SEO再レビュー: `R2合格`
- 編集・校正再レビュー: `R2合格`
- HTML変更: `未実施`
- 公開状態: `未公開`

## 既存実装の調査結果

### URLとファイル配置

- 既存コラム記事はサイトルート直下の英語スラッグ＋`.html`で公開されている
- 例: `/what-is-ai-video-production.html`、`/ai-video-vs-traditional-video.html`
- `/column/`配下のディレクトリ型URLは現行サイトで使用されていない
- 既存規則を優先し、新記事もルート直下に置く

### 記事ページ

- 代表テンプレート: `what-is-ai-video-production.html`
- headにはtitle、description、robots、canonical、OGP、X向けメタ情報がある
- JSON-LDは`@graph`でWebPage、BreadcrumbList、Organization、Articleなどを管理している
- 表示パンくずは「ホーム / お役立ち記事 / 記事名」
- 記事ヒーロー、公開日・更新日、導入、目次、本文セクション、関連サービス、問い合わせCTA、フッター、固定CTAの順
- CSSとJavaScriptは各HTML内に記載され、共通デザインをページ単位で再利用している

### 記事一覧

- `column.html`の`.article-list`内へ新しい順にカードを配置している
- カードはカテゴリー、タイトル、description相当の要約、公開日、リンクで構成される
- 860px以上で2列、それ未満は1列

### スマートフォン

- viewport指定あり
- 24pxの基本余白、可変フォント、1列レイアウト、モバイルナビを使用
- 640px、768px、1080pxを主な切り替え点としている
- `prefers-reduced-motion`と`noscript`の代替表示がある
- 新記事でも同じCSS、メニュー、固定CTA、フォーカス表示を再利用する

## 公開URL

- 公開パス: `/ai-video-outsourcing-checklist.html`
- 完全URL: `https://framepact.jp/ai-video-outsourcing-checklist.html`
- canonical: `https://framepact.jp/ai-video-outsourcing-checklist.html`
- 理由: 推奨された`/column/ai-video-outsourcing-checklist.html`より、既存記事のルート直下命名規則と整合する

## 作成予定ファイル

| ファイル | 内容 |
|---|---|
| `ai-video-outsourcing-checklist.html` | 承認済み公開本文を既存コラムデザインへ組み込む新規記事ページ |

## 変更予定ファイル

| ファイル | 変更内容 | 必須度 |
|---|---|---|
| `column.html` | 記事一覧の先頭へ新記事カードを追加 | 必須 |
| `sitemap.xml` | 新記事URLと`lastmod`を追加し、`column.html`の`lastmod`を実装日に更新 | 必須 |
| `what-is-ai-video-production.html` | 外注前の確認事項を知りたい読者向けに新記事への文脈リンクを追加 | 推奨 |
| `ai-video-price.html` | 見積条件を整理したい読者向けに新記事への文脈リンクを追加 | 推奨 |

承認済み本文そのものは変更しない。内部リンクを設置する場合も、既存ページ側に短い案内を追加するか、既存の関連リンク枠を利用する。

## 記事一覧への追加場所

- `column.html`の`.article-list`直下
- 現在先頭の`ai-video-vs-traditional-video.html`より前
- カテゴリー候補: `AI動画制作の外注・発注`
- 公開日: `2026年8月3日`
- タイトルと要約は承認済み原稿のtitle・descriptionに一致させる

## 内部リンク設計

### 新記事へのリンク元

| リンク元 | リンク先 | アンカー方針 |
|---|---|---|
| `column.html` | `/ai-video-outsourcing-checklist.html` | 承認済み記事タイトル |
| `what-is-ai-video-production.html` | `/ai-video-outsourcing-checklist.html` | `AI動画制作を外注する前の確認事項` |
| `ai-video-price.html` | `/ai-video-outsourcing-checklist.html` | `見積だけでなく外注条件を整理する5項目` |

### 新記事からのリンク先

| リンク先 | 役割 |
|---|---|
| `/what-is-ai-video-production.html` | AI動画制作の基礎説明 |
| `/ai-video-price.html` | 見積・費用要素の詳細 |
| `/no-material-ai-video.html` | 素材なし制作の詳細 |
| `/corporate-ai-video.html` | 企業向けサービス説明 |
| `/#contact` | 承認済み問い合わせ導線 |

本文へリンクを付ける際は、承認済み文言を変更せず、既存の語句へリンク属性を付ける。新しい説明文が必要な場合は、本文変更として実施前に提案する。

## メタ情報

- title: `企業がAI動画制作を外注する前に確認すべき5つの項目｜Framepact`
- description: 承認済みdescriptionをそのまま使用
- robots: `index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1`
- canonical: `https://framepact.jp/ai-video-outsourcing-checklist.html`
- OGP type: `article`
- OGP URL: canonicalと同一
- OGP image: 既存共通画像`https://framepact.jp/images/ogp-framepact.png`
- X card: `summary_large_image`

サイト実装上のブランド接尾辞`｜Framepact`は既存記事と同じメタ表現としてtitle要素に付ける。表示H1は承認済みタイトルを変更しない。

## 構造化データ

- JSON-LDの`@graph`を使用
- `WebPage`: URL、title、description、言語
- `BreadcrumbList`: ホーム、お役立ち記事、新記事
- `Organization`: FRAMEPACTの承認済み範囲だけを記載
- `Article`: headline、description、image、authorまたはpublisher、公開日、更新日、mainEntityOfPage、言語
- `datePublished`: `2026-08-03`
- `dateModified`: 初回実装時は`2026-08-03`
- FAQ本文がないため`FAQPage`は追加しない
- 既存テンプレートにある未承認の人物経歴は新記事へコピーしない

## パンくず

- 表示: `ホーム / お役立ち記事 / AI動画制作を外注する前の5項目`
- JSON-LD: 3階層で表示と一致させる
- 2階層目のリンク: `https://framepact.jp/column.html`

## CTA

- 記事本文内の承認済みCTAは`/#contact`へリンク
- ページ最下部は既存のCONTACTセクションを再利用
- CONTACTセクション内のボタンは既存Googleフォームへ遷移
- ヘッダー・モバイルメニュー・固定CTAはページ内`#contact`へ移動
- リンク先、`target="_blank"`、`rel="noopener"`、クリック計測は既存記事と同じ方式を再利用

## sitemap更新

- 次のURLを追加:
  - `https://framepact.jp/ai-video-outsourcing-checklist.html`
- 新記事の`lastmod`: `2026-08-03`
- 記事カードを追加する`https://framepact.jp/column.html`の`lastmod`も実装日に合わせる
- 既存URLの順序とXML形式を維持する

## 既存デザインへの影響

- 新しいデザインシステム、CSSファイル、JavaScriptライブラリは追加しない
- 既存記事のページヒーロー、目次、本文幅、交互背景、関連カード、CTA、フッターを再利用する
- 記事一覧は既存カードを1件追加するだけで、グリッド規則を変更しない
- 新規画像は必須とせず、OGPは既存共通画像を使用する
- 承認済み原稿の文章は変更しない

## 公開前テスト

1. HTML構文とJSON-LDの構文確認
2. title、description、H1、canonical、OGP URLの一致
3. H1が1件で、H2と目次アンカーが一致
4. 表示パンくずとBreadcrumbListの一致
5. Articleのheadline、description、公開日、更新日、URLの一致
6. 公開本文と承認済み原稿の文字列・段落単位の照合
7. 管理情報・申し送り・レビュー記録がHTMLへ混入していないこと
8. 料金、具体的納期、具体的修正回数、未承認実績が追加されていないこと
9. column一覧カード、本文内リンク、関連カード、CTA、privacyリンクのリンク切れ確認
10. Googleフォームは実送信せず、到達確認のみ
11. 390px、768px、1280pxで横スクロール、文字切れ、重なりを確認
12. モバイルメニュー、目次、固定CTA、フォーカス操作、Escape操作を確認
13. JavaScript無効時と`prefers-reduced-motion`時に本文が読めること
14. 画像、favicon、OGP画像の参照確認
15. sitemap.xmlのXML構文と新URLの重複確認
16. HTML変更後にSEO・編集の再レビュー条件へ該当する本文変更がないこと

## 実装開始判定

- 判定: `開始可能`
- 根拠: 企画、title、description、公開本文、CTA、原稿、公開実装がオーナー承認済みで、SEO R2・編集R2も合格している
- 実装時の制約: 承認済み本文を変更せず、管理情報を公開せず、未承認の人物実績や具体的条件を追加しない
- 現在の状態: `計画のみ。HTML、CSS、JavaScript、公開ページは未変更`
