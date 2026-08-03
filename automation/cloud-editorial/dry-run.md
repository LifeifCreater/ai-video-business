# ドライラン手順

## 目的

外部投稿、main更新、Cloudflare公開をせず、重複防止、承認停止、JSON生成、ブランチ命名を検証する。

## 手順

1. GitHub接続はread/write、main保護を有効にする。Cloudflareと投稿サービスの認証は渡さない。
2. Scheduled Taskを登録せず、各promptを手動で「DRY RUN。commit、push、PR作成禁止」と付けて実行する。
3. サンプルIDだけを使用し、既存の実企画・原稿を変更しない。
4. `workflowType:sourceId` が既存ならskippedになることを確認する。
5. active lockがある場合に停止し、期限切れlockを削除せずalertsへ出すことを確認する。
6. 正本未承認、verified期限切れ、外部情報取得失敗をそれぞれ模擬し、waiting_ownerまたはfailedになることを確認する。
7. JSON Schema、JSON構文、日時の `+09:00`、branch規則を確認する。
8. 朝会promptが読み取り専用で、publish queueの `approved + unpublished + 当日` だけを今日の候補にすることを確認する。
9. テスト後、サンプル以外の差分、外部投稿、main更新、Cloudflareデプロイがないことを確認する。

## 合格条件

- 同一案件を二重処理しない
- すべての書き込みジョブが専用ブランチとDraft PRで停止する
- 承認不足、上限、競合、テスト失敗を自動突破しない
- 秘密情報がGit差分とログにない
- Macを停止してもクラウド側の手動ドライランが完了する
