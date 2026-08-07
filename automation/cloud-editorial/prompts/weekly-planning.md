# Scheduled Task Prompt: 週次企画会議

実行: 毎週日曜 02:00 Asia/Tokyo

GitHub上のFRAMEPACTリポジトリを正本として週次企画会議を実行する。開始前に `automation/cloud-editorial/job-register.json` と `locks.json` を確認し、`weekly_planning:WEEK-YYYY-MM-DD` がrunning、waiting_owner、completed、またはPR作成済みなら重複実行しない。stale lockは削除せず朝会alertsへ記録して停止する。

1. `business/`、`planning/`、公開済みHTML、企画・原稿・媒体台帳を読む。
2. 過去記事との重複、カニバリ、同じCTAの連続を確認する。
3. 直近30日の公式発表・一次情報を優先して候補を調査する。アクセス不可、日付不明、第三者情報だけの事項を事実として採用しない。
4. FRAMEPACTとの関係、企業担当者の実務課題、問い合わせへの近さを評価し、候補を最大10件、推奨企画を最大3件に絞る。
5. `planning/drafts/` に1企画1ファイルで保存し、`planning/idea-register.md` を更新する。
6. 専用ブランチ `planning/weekly-YYYY-MM-DD` を既存なら再利用し、commit・pushしてDraft PRを作る。
7. jobを `waiting_owner`、approvalRequiredを `planning_owner_approval` として停止する。
8. `runtime-state-update.md`に従い、本文を含まない実行結果を`data/editorial-state`へ同期する。

未承認企画を執筆、HTML化、公開、投稿しない。mainへpushしない。状態台帳にも企画本文・タイトル・要約を複製しない。コンフリクトを自動解決しない。秘密情報をログやファイルへ書かない。
