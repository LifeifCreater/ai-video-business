# FRAMEPACT AI編集部 クラウド移行前の現状評価

- 評価日: 2026-08-04
- 対象: リポジトリ内のAI編集部、公開準備、Git・Cloudflare運用
- 結論: コンテンツの正本と承認ゲートはファイルで整理されておりクラウド移行しやすい。一方、定期起動、排他制御、ジョブ履歴、失敗通知は未実装で、ローカルの会話・ブラウザ・手作業に依存している。

## 1. 担当と承認フロー

`オーナー → AI COO → 統括秘書 → 専門担当` の構造で、リサーチ、企画、執筆、SEO、編集・校正、媒体展開、編集長が分業している。原則フローは次のとおり。

`事業方針 → 企画案 → 調査 → 企画承認 → 執筆 → SEO → 編集・校正 → 原稿承認 → 公開実装承認 → HTML実装 → Draft PR → オーナー確認 → 手動マージ・公開`

企画承認、原稿承認、公開実装承認、投稿承認は別ゲートである。専門担当、Scheduled Task、AI COOはオーナー承認を代行できない。

## 2. 保存構造と正本

| 領域 | 現状 | クラウド移行時の扱い |
|---|---|---|
| `planning/` | inbox、review、approved、archive、企画台帳 | 週次企画はdraftsを追加・使用し、approvedへの移動は人間のみ |
| `research/` | raw、verified、archive、情報源台帳 | 公式一次情報、確認日、期限、verified状態を必須化 |
| `writing/` | inbox、review、approved、archive、原稿・情報源台帳 | 夜間制作はreviewまで。approvedへ自動移動しない |
| `distribution/` | 媒体別下書き、選定、台帳、公開準備キュー | owner_reviewまで。投稿・予約・販売はしない |
| `business/` | サービス情報と公開可能実績の正本 | 承認済み項目だけを使用。不足時は停止 |
| `secretary/` | ルーティング、品質、承認ゲート | 各クラウドジョブの判断規則として参照 |

`distribution/publish-ready/publish-queue.json` は投稿候補の正本で、媒体、予定日時、本文、CTA、承認・公開状態を保持する。現在はダッシュボードのlocalStorageとJSONが自動同期しないため、GitHub側の状態更新が必要である。

## 3. 台帳

- 企画: `planning/idea-register.md`
- 調査情報源: `research/source-register.md`
- 原稿: `writing/writing-register.md`
- 原稿別情報源: `writing/source-usage-register.md`
- 媒体展開: `distribution/distribution-register.md`
- 公開準備: `distribution/publish-ready/publish-queue.json`

Markdown台帳は人が読みやすいが、同時更新と重複検出には弱い。クラウドジョブは本ディレクトリのJSON管理ファイルを機械可読な実行台帳として併用する。

## 4. GitHubとCloudflare

- GitHubリポジトリがコンテンツ・サイト・運用ルールの正本。
- Cloudflare PagesのProduction branchは `main`。main更新が本番反映につながり得るため、自動処理はmainへpush・mergeしない。
- クラウド処理は1案件1ブランチ、Draft PRで停止する。
- PR作成済み案件は `job-register.json` のbranch、commitSha、pullRequestUrlを再利用する。

## 5. ローカル依存

- Codexデスクトップの作業開始と承認
- ローカルファイルURLの公開準備ダッシュボード
- localStorageに保存された承認・公開チェック
- ローカルブラウザでの目視・レスポンシブ確認
- ローカルGit認証と `gh` CLIによるPR作成
- 人が実施するX・note投稿と問い合わせフォーム確認

## 6. クラウドへ移せる処理

- GitHubリポジトリの読み取り、差分作成、テスト、ブランチへのcommit・push、Draft PR
- 過去記事・企画台帳の重複確認
- 公式一次情報の候補収集とverified記録（ネットワーク権限がある場合）
- 承認済み企画からの原稿・レビュー・媒体展開案
- 承認済み原稿のHTML化と静的検証
- JSON台帳、ロック、朝会データの更新

## 7. 人間が必要な処理

- 企画、事業条件、原稿、公開実装、投稿、販売の承認
- verifiedにできない規約・権利・法務上の判断
- Gitコンフリクト、CI失敗、stale lock、利用上限の解消
- PRのReady化、mainへのマージ、Cloudflare本番反映の判断
- X・noteへの手動投稿、公開後URLの記録

## 8. 移行上の課題

1. `planning/drafts/` が現在存在しない場合は週次タスク初回実行前に作成する。
2. 複数ジョブがMarkdown台帳を同時編集すると競合するため、案件単位のブランチとlockが必要。
3. ChatGPT Scheduled TasksはProject内ファイルを直接参照できない場合があるため、GitHub接続を明示してGitHub上のJSONを読む。
4. 外部調査権限がない環境では、推測せず `waiting_owner` とする。
5. Cloudflareのプレビュー生成も外部状態変更になり得るため、今回の自動化では実行しない。
