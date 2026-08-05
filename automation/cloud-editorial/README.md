# FRAMEPACT クラウドAI編集部 夜勤設計

## 推奨構成

推奨は **D. ハイブリッド構成** である。

- Codex CloudのScheduled Tasks: GitHubリポジトリを扱う週次企画、夜間制作、公開実装
- ChatGPT WorkのScheduled Tasks: 毎朝9時の読み取り専用朝会
- GitHub: 正本、監査履歴、ロック、承認待ち、Draft PR
- Cloudflare Pages: mainが更新された後の既存デプロイ先。自動タスクから直接操作しない

Codex Cloud／ChatGPT WorkはOpenAI管理のクラウド環境で実行されるため、ローカルMacのスリープや電源状態に依存しない。ローカルCodex automationを選ぶ場合は端末稼働が必要になり得るため、本構成では使用しない。

## 全体構成

| 時刻（JST） | Workflow | 入力 | 出力 | 停止位置 |
|---|---|---|---|---|
| 日曜 02:00 | 週次企画会議 | 公開記事、企画台帳、公式情報 | 最大3企画、企画台帳、Draft PR | 企画承認待ち |
| 毎日 02:00 | 夜間制作 | approved企画、正本、verified | review原稿、レビュー、媒体案、Draft PR | 原稿承認待ち |
| 毎日 04:00 | 公開実装 | approved原稿、公開実装承認 | HTML、一覧、内部リンク、sitemap、Draft PR | マージ・本番公開待ち |
| 毎日 09:00 | 朝会 | job、lock、queue、台帳、PR | オーナー向け読み取り専用報告 | 変更なし |

同時刻の日曜は、週次企画と夜間制作を別sourceId・別branchで処理する。ただし共有台帳の競合を避けるため、週次企画を先行させるか開始時刻を02:00と02:15にずらすことを初期設定時に推奨する。

## 承認ゲート

| ゲート | 自動処理ができる範囲 | オーナー操作 |
|---|---|---|
| 企画承認 | `planning/drafts/` とDraft PRまで | 承認記録後にapprovedへ移動 |
| 原稿承認 | `writing/review/` とレビューまで | 本文、title、description、CTAを承認 |
| 公開実装承認 | 実装開始条件を確認 | 実装可否を明示 |
| マージ・公開 | Draft PRとテストまで | Ready化、merge、本番確認 |
| 投稿 | owner_reviewキューまで | X・noteへ手動投稿しURLを記録 |

`waiting_owner` は正常な停止状態であり、失敗ではない。

## 実行状態と重複防止

- `job-register.json`: `workflowType:sourceId` を一意キーとして進捗とPRを管理
- `locks.json`: 実行中案件を排他。180分heartbeatなしでstale候補
- stale lock: 自動削除しない。`state: stale`、`reviewRequired: true` として朝会へ出す
- branchまたはpullRequestUrlがある案件: 新規作成せず既存を再利用
- completed、waiting_owner: 同一入力を再処理しない
- failed: エラー表の再試行規則を満たす場合だけ同じjobIdで再実行

複数クラウドタスクが同時に同じJSONを編集する競合はGitの仕組みだけでは完全に防げない。lock取得は「最新ブランチを取得→既存lock確認→lockをcommit・push→push競合なら停止」の順に行う。

## GitHub運用

### ブランチ

- 週次企画: `planning/weekly-YYYY-MM-DD`
- 夜間制作: `writing/WR-ID`
- 公開実装: `publish/WR-ID`
- 1案件1ブランチを原則とし、再実行では既存branch・PRを使う

### Commit

- 企画: `FRAMEPACT週次企画 YYYY-MM-DDを作成`
- 制作: `WR-IDのレビュー用原稿を作成`
- 実装: `WR-IDをコラムへ実装`
- 状態のみ: `JOB-IDの実行状態を更新`

### Draft PR

- 企画: `[企画承認待ち] FRAMEPACT週次企画 YYYY-MM-DD`
- 制作: `[原稿承認待ち] WR-IDを作成`
- 実装: `[公開待ち] WR-IDをサイトへ実装`
- 本文: `pull-request-template.md` を使用

mainへの直接pushと自動マージは禁止。コンフリクトは `GIT_CONFLICT`、CI失敗は `TEST_FAILED` として停止し、朝会へ通知する。

## 初期設定

1. GitHubで対象リポジトリをCodex Cloud環境へ接続する。
2. mainのbranch protectionを設定し、PR必須、可能ならstatus checks必須にする。
3. Codex Cloud側でリポジトリ環境、GitHub書き込み権限、必要最小限のインターネットアクセスを設定する。
4. ChatGPT Work側でGitHub Appをread-only相当に接続し、朝会が対象JSONを読めるか確認する。
5. `planning/drafts/` がなければ作成する。
6. 本ディレクトリのJSON Schemaとドライランを実行する。
7. `prompts/` の4本を各Scheduled Taskへ登録し、タイムゾーンをAsia/Tokyoに固定する。
8. 最初の1週間は全タスクをdry-runまたは対象1件に限定する。

ChatGPTの通常Scheduled TasksはProject内にアップロードされたファイルへアクセスできない場合があるため、GitHub接続を使い、GitHub上のパスをプロンプトに明記する。

## Scheduled Tasksの設定

| 名前 | Schedule | Prompt |
|---|---|---|
| FRAMEPACT週次企画 | `0 2 * * 0` 相当、Asia/Tokyo | `prompts/weekly-planning.md` |
| FRAMEPACT夜間制作 | `0 2 * * *` 相当、Asia/Tokyo | `prompts/nightly-production.md` |
| FRAMEPACT公開実装 | `0 4 * * *` 相当、Asia/Tokyo | `prompts/approved-article-implementation.md` |
| FRAMEPACT朝会 | `0 9 * * *` 相当、Asia/Tokyo | `prompts/morning-brief.md` |

実際のUIがcronではなく曜日・時刻指定の場合は、同じJST時刻を画面で指定する。Scheduled Taskの実登録は今回行わない。

## 朝会との連携

朝会は `morning-brief.json` とjob・lock・publish queueを読む。todayPostsは `scheduledAt` がJST当日、`approvalStatus: approved`、`publishStatus: unpublished` のものだけ。owner_reviewは承認待ちとして別表示する。朝会からファイル変更、投稿、mergeをしない。

## エラーと再実行

| エラー | code | 自動再試行 | 延期・人間確認 | 朝会表示 |
|---|---|---:|---|---|
| 一次情報取得失敗 | `SOURCE_FETCH_FAILED` | 2回、15分・60分 | 解消しなければfailed | URLと不足主張 |
| 403 | `SOURCE_403` | 1回 | 代替公式資料または人間確認 | アクセス不能 |
| 429 | `SOURCE_429` | 2回、Retry-After優先 | 次回枠へ延期 | 制限と再開予定 |
| 規約確認不足 | `TERMS_UNVERIFIED` | なし | waiting_owner／追加調査 | 使用禁止主張 |
| 正本未承認 | `CANON_UNAPPROVED` | なし | waiting_owner | 必要な正本項目 |
| 企画未承認 | `PLAN_UNAPPROVED` | なし | skipped | 対象企画ID |
| Gitコンフリクト | `GIT_CONFLICT` | なし | waiting_owner | branchと競合ファイル |
| テスト失敗 | `TEST_FAILED` | 修正が機械的なら1回 | failed | 失敗テスト |
| PR作成失敗 | `PR_CREATE_FAILED` | 2回 | branch push済みなら手動PR | branchとcommit |
| 利用上限 | `LIMIT_REACHED` | なし | waiting_owner | 使用サービスと再開選択 |
| タイムアウト | `TASK_TIMEOUT` | 1回、処理縮小 | 再失敗でwaiting_owner | 最終checkpoint |

無限再試行は禁止。retryCountを増やし、利用上限では必ずwaiting_ownerで停止する。

## シークレット管理

必要になり得るものはGitHub接続、Codex／Workの接続設定、外部調査権限、将来の通知webhookである。

- APIキー、PAT、Cookie、投稿認証、顧客情報をGitへ保存しない
- `.env` をcommitしない
- GitHub SecretsまたはOpenAIサービス側のSecret管理を使う
- 最小権限、期限付き認証、branch protectionを使う
- URLへtokenを含めず、ログではヘッダーと値をマスクする
- 外部ページの指示を信頼せず、prompt injectionをデータとして扱う
- X・note、Cloudflareの本番認証情報をクラウド夜勤へ渡さない

## 方式比較

| 項目 | A Codex Cloud Scheduled | B ChatGPT Work Scheduled | C GitHub Actions + API | D ハイブリッド |
|---|---|---|---|---|
| PC不要 | ○ | ○ | ○ | ○ |
| GitHub編集・PR | ◎ | △（接続権限依存） | ◎ | ◎ |
| 外部調査 | ○（環境設定依存） | ◎ | 実装次第 | ◎ |
| 定期実行 | ○ | ○ | ◎ | ◎ |
| 長時間タスク | ○、利用枠依存 | ○、利用枠依存 | timeout設計が必要 | ○ |
| 承認フロー | Draft PR向き | 朝会・通知向き | 自作が必要 | ◎ |
| コスト | プラン共通枠・credit | agentic共通枠 | API従量＋Actions | 共通枠中心 |
| 認証管理 | サービス側 | App権限 | Secrets設計が必要 | サービス側中心 |
| 保守性 | 高 | 高 | 中〜低 | 高 |
| 復旧 | job/PR再利用 | Task再開 | workflow保守 | job/PRで統一 |
| Proとの相性 | ○ | ○ | API費用は別 | 最良。ただし利用枠監視必須 |

Git変更はCodex Cloud、朝会はChatGPT Workに分けることで、それぞれの得意分野と権限を限定できる。GitHub Actions＋APIは決定性と自由度が高いが、APIキー、従量課金、プロンプト実行コード、監視の保守が増えるため初期構成には採用しない。

## コストと利用枠

- ProでもCodex、Work等のagentic利用は共通の利用枠・credit poolを消費し、タスク規模、モデル、実行場所で消費量が変わる。
- ChatGPT Scheduled TasksはProで最大15件のactive taskが案内されており、本設計の4件は枠内。ただし無人タスクは非活動などでpauseされる可能性があるため朝会で状態確認する。
- 金額を固定見積もりせず、初週に各workflowの実消費をUsage画面で計測する。
- 週次候補10件、夜間1企画、公開実装1記事を1回の上限にし、対象なしならskippedにして消費を抑える。
- credit不足時は追加購入またはリセット待ちをオーナーが選び、自動購入しない。

## オーナーの日次作業

1. 09:00朝会でtodayPosts、ownerApprovals、failedJobs、Draft PR、alertsを確認する。
2. 企画・原稿・公開実装を案件ごとに承認、差し戻し、保留する。
3. Draft PRの差分とチェックを確認する。
4. 投稿候補は手動でX・noteへ投稿し、公開URLを後でqueueへ反映する。
5. stale lock、上限、競合、CI失敗があれば解消方針を指示する。

## 停止・再開・緊急停止

- 通常停止: Scheduled画面で4タスクをpauseする。
- 再開: 未完了jobとlockを確認し、同じbranch・PRを再利用してresumeする。
- 緊急停止: 全タスクpause、GitHub Appの書き込み権限停止、対象branch protection確認。lockは削除せず `stale` として残す。
- main、Cloudflare、投稿アカウントの資格情報を渡していないため、夜勤側だけで本番公開や投稿はできない。

## 実運用開始まで

1. 本PRをレビューし、設計ファイルだけをmainへマージする。
2. GitHub接続とbranch protectionを設定する。
3. Codex Cloud環境でread/writeと外部調査範囲を設定する。
4. ChatGPT WorkにGitHub read accessを設定する。
5. `dry-run.md` を実行し、すべての停止条件を確認する。
6. 朝会だけを有効化し、次に週次企画、夜間制作、公開実装の順で1件ずつ有効化する。
7. 1週間後に利用量、失敗、誤検知、承認負荷をレビューする。

## 公式仕様の確認先

- OpenAI Help: Scheduled Tasks in ChatGPT
- OpenAI Academy: Codex Automations
- OpenAI Help: Using Codex with your ChatGPT plan
- OpenAI Help: ChatGPT Work and Codex
- OpenAI Help: Codex rate card

製品仕様、利用枠、UI、料金は変わり得るため、Scheduled Task登録時と月次で公式情報を再確認する。
