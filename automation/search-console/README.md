# Search Console自動運用

## 推奨構成

GitHub Actionsを実行基盤、GitHubの専用stateブランチを監視状態の正本、Search Console APIを取得・送信先とする。MacやPCは処理に参加しない。

- 08:30 JST: URL Inspection APIで対象URLを確認し、朝会データを生成
- Cloudflare本番デプロイ成功時: sitemapとlastmodを検証し、Sitemaps APIで再送信
- 09:00 JST: AI編集部朝会が `morning-brief.json` の `searchConsole` を最大5件表示
- 状態更新は `state/search-console-monitor` とDraft PRへ保存し、mainへ直接pushしない

通常記事にIndexing APIは使用しない。URL Inspection APIはGoogleインデックス上の状態確認だけに使い、ライブテストやインデックス登録リクエストは行わない。登録は保証しない。

## 初期設定

1. Google CloudプロジェクトでSearch Console APIを有効化する。
2. 専用service accountを作成する。
3. Search Consoleの `https://framepact.jp/` プロパティへservice accountのメールアドレスを「フル」ユーザーとして追加する。sitemap送信に必要だが、所有者権限は付与しない。
4. service account JSONをGitHub Actions Secret `GSC_SERVICE_ACCOUNT_JSON` に登録する。ファイルや`.env`としてcommitしない。
5. Cloudflare Pagesの本番成功がGitHubの`deployment_status`（environment=`production`、environment URLがframepact.jp）へ反映されることを確認する。反映されない場合、sitemap送信は起動しない。
6. ActionsのWorkflow permissionsをRead and writeにし、Pull Requestsの作成を許可する。

GitHub接続にはActions標準の短命な`GITHUB_TOKEN`を使い、追加PATは原則不要。

## 判定と再確認

本番deployment成功後、sitemap内のURLとlastmodを台帳に照合し、前回送信から6時間以上の場合だけ再送信する。08:30の検査対象は公開1日後の未検査URL、前回未登録、`retryAfter`到来、オーナー対応中のURLとする。

公開7日後も未登録、robots.txtブロック、noindex、canonical不一致、404/5xx、sitemap未掲載、クロール済み・未登録の継続、API取得3回連続失敗をオーナー対応にする。公開7日未満で未登録だけの場合は経過観察とする。

## Secretと安全性

- 必須Secret: `GSC_SERVICE_ACCOUNT_JSON`
- リポジトリへ鍵、token、OAuth client secretを保存しない
- ログへSecretを表示しない
- fork PRではSecretを渡さない。本workflowはPRイベントでは起動しない
- service accountはFRAMEPACTプロパティだけに追加する
- 投稿、Indexing API、画面自動操作、Cloudflare再デプロイを行わない

## dry-run

```sh
python3 automation/search-console/search_console_automation.py inspect
python3 automation/search-console/search_console_automation.py submit
```

`--live`を付けない限りAPI通信もファイル更新も行わない。GitHub Actionsの初回手動実行でも`dry-run`を選ぶ。

401/403は権限・プロパティ名を確認し、自動再試行しない。429/5xxは翌日に延期する。3回連続失敗でオーナー対応へ上げる。state PRの競合は自動解決しない。

## 公式仕様

- Sitemaps API: `sitemaps.submit`（書込scope）
- URL Inspection API: `index.inspect`（読取scopeで利用可能）
- Search Console APIはOAuth 2.0認証を使用
