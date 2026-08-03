# Scheduled Task Prompt: AI編集部朝会

実行: 毎日 09:00 Asia/Tokyo

GitHub接続を使い、mainおよび未処理Draft PRにある次のファイルを読み取り専用で確認する。

- `automation/cloud-editorial/job-register.json`
- `automation/cloud-editorial/locks.json`
- `automation/cloud-editorial/morning-brief.json`
- `distribution/publish-ready/publish-queue.json`
- 企画、原稿、媒体展開の各台帳

日本時間の当日について、承認済み・未公開の投稿、オーナー承認待ち、夜間完了、失敗、Draft PR、次回予定、週間進捗、stale lockと利用上限を簡潔に提示する。ファイル、PR、承認状態、投稿状態を変更しない。`owner_review` を承認済みとして扱わない。投稿、予約、マージ、公開を行わない。

`scheduledAt` が現在の日本時間より過去で `publishStatus: unpublished` の投稿は、削除、再予約、公開済みへの変更をせず「期限超過の未公開投稿」としてalertsへ分離する。投稿時刻の再設定と公開済み判断はオーナー確認事項とする。
