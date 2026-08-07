# Scheduled Task Prompt: 夜間制作

実行: 毎日 02:00 Asia/Tokyo

GitHub上のFRAMEPACTリポジトリを正本として夜間制作を実行する。対象は `planning/approved/` のうち、同じ企画IDのcompleted、waiting_owner、既存Draft PR、active lockがなく、対応する原稿が `writing/review/` または `writing/approved/` に存在しない未処理企画に限る。案件ごとに `nightly_production:PLAN-ID` を重複キーとして取得する。

対応する原稿、公開HTML、sitemap登録、またはマージ済みPRが確認できた企画は再制作しない。jobに履歴がない場合は既存成果物とGit履歴を照合し、既存のbranch、commit、PRをcompletedとして記録して停止する。判断できない場合は `waiting_owner` とし、新規原稿やPRを作らない。

開始条件をすべて満たすこと。

- 企画承認者と承認日が記録済み
- 必要な `business/` 正本項目が承認済み
- 必要な外部事実が `research/verified/` で有効、または公式一次情報から検証可能
- CTA、対象読者、目的、主要メッセージが明確

処理:

1. 不足情報を公式一次情報から調査し、公開日、確認日、対象版、再確認期限を記録する。確認できなければ断定せず停止する。
2. 企画に従って原稿を作成し、事実確認、正本整合、SEO、編集・校正を別記録として実施する。
3. 完成候補を `writing/review/` に保存する。`writing/approved/` へ移動しない。
4. X・noteの媒体展開案を作成し、編集レビュー済み候補だけを `publish-queue.json` へ `approvalStatus: owner_review`、`publishStatus: unpublished` で追加する。
5. `writing/WR-ID` ブランチを再利用または作成し、commit・push、Draft PRを作る。
6. jobを `waiting_owner`、approvalRequiredを `article_owner_approval` として停止する。
7. `runtime-state-update.md`に従い、本文を含まない実行結果を`data/editorial-state`へ同期する。

原稿の自動承認、HTML公開実装、投稿、予約、PRマージ、mainへのpushは禁止。状態台帳にも原稿・投稿本文、タイトル、要約を複製しない。利用上限は再試行せず `LIMIT_REACHED` でwaiting_ownerにする。
