# 2026-10-31 コラム公開実装

オーナーの「10/3以降の未掲載記事を全て反映」「noteへの誘導を全て削除」「全てマージまで」の依頼に基づく。対象はレビュー済み完成原稿5本。企画だけの項目や他媒体の原稿は対象外。

| 原稿ID | 原稿作成日 | 公開日表示 | 公開先 |
|---|---|---|---|
| WR-20261025-001 | 2026-10-25 | 2026-10-31 | https://framepact.jp/training-video-playback-speed-checklist.html |
| WR-20261025-002 | 2026-10-25 | 2026-10-31 | https://framepact.jp/video-audio-track-extraction-checklist.html |
| WR-20260927-003 | 2026-10-09 | 2026-10-31 | https://framepact.jp/document-to-video-summary-governance.html |
| WR-20260920-001 | 2026-10-08 | 2026-10-31 | https://framepact.jp/training-video-structure.html |
| WR-20260927-002 | 2026-10-07 | 2026-10-31 | https://framepact.jp/published-video-replacement-rollback.html |

原稿本文は既存のレビュー済み正本から変換。管理情報・内部メモは公開本文から除外。タイトル・description・canonical・Article構造化データ・目次・横スクロール表・サービスへのリンク・逆リンク・記事一覧・sitemapを実装。Google Vidsの公式発表は2026-10-31に再確認（速度記事のモバイルURLと音声抽出記事）。ヘルプの確認日は既存の2026-10-30を維持。実機動作・問い合わせ送信は未試験。

公開用HTML実装と本番反映を区別する。本番公開の成否は本PRマージ後のCloudflare buildとProduction smoke checkを正本とする。日付は原稿作成日に遡らせない。X/note投稿・予約・キューや契約・計測設定は変更しない。
