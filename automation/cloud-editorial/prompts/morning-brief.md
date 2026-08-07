# Scheduled Task Prompt: AI編集部朝会

実行: 毎日 09:00 Asia/Tokyo

GitHub接続を使い、mainの正本と`data/editorial-state`の実行状態台帳を読み取り専用で確認する。Draft PRブランチの本文を実行状態の集計元にしない。

- `automation/cloud-editorial/job-register.json`
- `automation/cloud-editorial/locks.json`
- `automation/cloud-editorial/morning-brief.json`
- `data/editorial-state`ブランチの`automation/cloud-editorial/runtime-state.json`
- `distribution/publish-ready/publish-queue.json`
- 企画、原稿、媒体展開の各台帳

日本時間の当日について、承認済み・未公開の投稿、オーナー承認待ち、夜間完了、失敗、Draft PR、次回予定、週間進捗、stale lockと利用上限を簡潔に提示する。最終実行日時と実行結果はruntime-stateを優先し、本文と承認状態はmainの正本だけで判定する。ファイル、PR、承認状態、投稿状態を変更しない。`owner_review` を承認済みとして扱わない。投稿、予約、マージ、公開を行わない。

`scheduledAt` が現在の日本時間より過去で `publishStatus: unpublished` の投稿は、削除、再予約、公開済みへの変更をせず「期限超過の未公開投稿」としてalertsへ分離する。投稿時刻の再設定と公開済み判断はオーナー確認事項とする。

朝会生成時に、当日中は固定するモバイルエイリアス `article1`、`article2`、`x1`、`x2`、`note1`、`note2` を作る。各値は `alias`、`canonicalId`、`platform`、`title`、`scheduledAt`、`approvalStatus`、`publishStatus`、`pullRequestUrl`、`sourceUrl`、`generatedAt` を持ち、対象がなければnullとする。投稿用エイリアスには `approvalStatus: approved`、`reviewStatus: editor_in_chief_passed`、`publishStatus: unpublished` の当日候補だけを時刻順で割り当てる。記事用エイリアスには、オーナー最終承認待ちまたは公開実装承認済みで未公開のopen PRだけを割り当てる。すでにmainへ実装済みの原稿は割り当てない。

同じJST日付の朝会を再表示するときは既存の対応を維持し、候補の並び順や状態変化だけで別コンテンツへ付け替えない。状態が変わった項目は元のaliasのまま状態を更新し、翌日の朝会生成時にだけ再割当する。ChatGPTの初期表示は「今日やること」と、`記事N確認`、`記事N公開`、`XN`、`noteN`、`KPI` の操作候補だけにする。

Search Consoleについては、open中の `state/search-console-monitor` Draft PRがあればその `automation/cloud-editorial/morning-brief.json` を優先し、なければmainを読む。`searchConsole` を重要度順に最大5件だけ表示する。新規公開URL数、登録済み数、未登録数、エラー数、canonical不一致数、sitemap未掲載数、オーナー対応URL、次回確認予定を示す。nullは未取得であり、0または正常と解釈しない。
