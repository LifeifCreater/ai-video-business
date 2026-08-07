# AI編集部実行状態台帳の更新規約

週次企画、夜間制作、公開実装は、成果物ブランチの処理終了後に`data/editorial-state`ブランチの`automation/cloud-editorial/runtime-state.json`を更新する。

- 台帳へ保存できるのは実行ID、workflow種別、source ID、開始・終了日時、処理結果コード、成果物ブランチ、commit SHA、Draft PR番号・URL・状態、エラーコードだけ。
- 原稿本文、投稿本文、タイトル、要約、公開HTML、承認済み・公開済みという派生判定は保存しない。
- `waiting_owner`は承認済みへ変換せず、`failed`は完了へ変換しない。
- 同じ`runId`は上書き更新し、異なるrunは追記する。最新100件だけを保持する。
- 許可フィールド検証とupsertには`python automation/cloud-editorial/update_runtime_state.py --state automation/cloud-editorial/runtime-state.json --run-file RUN.json`を使う。手作業で本文フィールドを追加しない。
- 初回はmainから`data/editorial-state`を作成してよいが、mainへ直接pushしない。
- 更新直前に状態ブランチをfetchし、最新台帳へ自分のrunだけを`runId`でupsertして通常pushする。non-fast-forwardの場合は、作業中の台帳をpushし直さず、リモートの最新`runtime-state.json`を取得し直してから自分のrunだけを再upsertする。
- pushの再試行は1回（初回と合わせて最大2回）だけとし、force pushは禁止する。他タスクのrunを削除したり、台帳ファイル全体を古い内容で置換したりしない。
- 再取得、再upsert、通常pushのいずれかが失敗した場合は`STATE_SYNC_FAILED`として失敗終了する。成果物の承認・公開状態を変更せず、main、成果物ブランチ、既存の状態台帳へ追加の書き込みを行わない。
- JSON Schemaは`automation/cloud-editorial/schemas/runtime-state.schema.json`を使用する。
