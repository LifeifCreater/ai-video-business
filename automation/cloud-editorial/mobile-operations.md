# FRAMEPACT AI編集部モバイル運用設計

## 1. 目的

オーナーはChatGPTだけを操作し、GitHub、PR、Cloudflare、媒体台帳を直接開かずに次を行う。

- 記事の最終公開承認
- X・note原稿の表示とコピー
- 手動投稿後の公開状態記録
- PRのReady化、検査、merge
- 公開結果とKPIの確認

GitHubを正本、ChatGPTを唯一の操作画面とする。X・noteへの投稿そのものはオーナーが各媒体で手動実行する。認証情報は会話、Git、ログへ保存しない。

## 2. 構成

```text
オーナーのスマートフォン
        ↓ 短い日本語コマンド
ChatGPT モバイル編集部コンソール
        ↓ 読み取り／承認済み操作
GitHub（main、台帳、queue、job、PR）
        ↓ 記事PRのmerge時のみ
Cloudflare（main連動デプロイ）

X・noteはオーナーが手動投稿
        ↓ 投稿URLをChatGPTへ返信
ChatGPTが状態専用PRでGitHub正本を更新
```

ChatGPTは毎回mainを読み直し、会話履歴だけで状態を判断しない。GitHub操作にはContents、Pull requests、Checksの必要最小限の権限が必要である。CloudflareのAPIキーは扱わず、既存のmain連動デプロイとデプロイ結果の読み取りを利用する。

## 3. 朝会UI

毎朝9時の最初の画面は「今日やること」だけを表示する。

```text
今日やること

記事
・記事1　公開承認待ち「タイトル」

X
・X1　08:10「タイトル」

note
・note1　12:15「タイトル」

確認
・承認待ち 1件
・失敗 0件

使える操作：記事1確認 / 記事1公開 / X1 / note1 / KPI
```

朝会の初期表示では長文、GitHubのパス、commit SHA、内部管理情報を出さない。問題がある場合だけ「要確認」を1行で示し、`詳細` で展開する。

参照順序:

1. `automation/cloud-editorial/morning-brief.json`
2. `distribution/publish-ready/publish-queue.json`
3. `automation/cloud-editorial/job-register.json` と `locks.json`
4. writing、planning、distribution、KPIの各台帳
5. GitHub上のPR、Checks、mainとの差分

## 4. モバイル用エイリアス

- `記事1`、`X1`、`note1` は朝会生成時に安定IDへ対応付ける。
- X・noteは `PUB-X-001` など既存の投稿IDを正本IDとする。
- 記事は原稿IDと公開実装PRを正本IDとする。
- 番号は当日の朝会内で固定し、並び替えで別IDへ付け替えない。
- 翌日に番号を再利用できるが、前日の会話から操作された場合はタイトルと正本IDを再確認する。
- 対応先が一意でない、PRが変わった、状態が更新された場合は実行せず確認を求める。

ChatGPTは書き込み操作の直前に、エイリアス、タイトル、正本ID、現在状態をmainから再取得する。

朝会は `morning-brief.json` に次の派生情報を生成する。これは操作対象を特定するための索引であり、承認・公開状態の正本は各台帳、job、PR、queueである。

```json
{
  "mobileAliases": {
    "articles": [
      {
        "alias": "記事1",
        "sourceId": "WR-ID",
        "title": "記事タイトル",
        "pullRequestUrl": "https://github.com/OWNER/REPO/pull/NUMBER",
        "approvalStatus": "owner_review",
        "publishStatus": "unpublished"
      }
    ],
    "x": [{ "alias": "X1", "sourceId": "PUB-X-ID" }],
    "note": [{ "alias": "note1", "sourceId": "PUB-NOTE-ID" }]
  }
}
```

記事の `publishStatus` は、writing台帳、公開実装job、PR、main上のHTML、Cloudflare結果から生成する。派生情報だけを変更して公開済みにしない。

## 5. コマンド

| オーナー入力 | ChatGPTの動作 | 外部状態変更 |
|---|---|---|
| `朝会` / `今日` | 今日やることだけを再表示 | なし |
| `記事1確認` | title、description、URL、PR状態、Checks、残る注意を表示 | なし |
| `記事1承認` | 原稿・公開実装承認を状態専用PRへ記録 | GitHubのみ |
| `記事1公開` | 公開ゲート確認後、PR Ready、merge、Cloudflare結果確認、公開状態記録 | あり |
| `X1` | 本文、記事URL、ハッシュタグ、完成形をコピーしやすく表示 | なし |
| `note1` | タイトル、本文、CTA、ハッシュタグを個別表示 | なし |
| `X1投稿した URL` | URLと対象を確認し、published状態をGitHubへ記録 | GitHubのみ |
| `note1投稿した URL` | URLと対象を確認し、published状態をGitHubへ記録 | GitHubのみ |
| `KPI` | 最新KPIの要約を表示 | なし |
| `KPI詳細` | 定義、期間、取得元、未取得理由まで表示 | なし |

`公開`、`投稿した`、`承認`は書き込み命令として扱う。対象が不明確な場合は推測せず停止する。

## 6. X表示

`X1` への返答は次の順序とする。

1. 本文
2. 記事URL
3. ハッシュタグ
4. 本文＋URL＋ハッシュタグの完成形

完成形は一つのコードブロックに入れ、管理情報を混ぜない。文字数超過、URL欠落、未承認、期限切れverifiedがあれば完成形を出さず警告する。表示だけでは投稿済みに変更しない。

## 7. note表示

`note1` への返答は次の順序とする。

1. タイトル
2. 本文
3. CTA
4. ハッシュタグ
5. 元記事URL

各要素を個別にコピーできる形で表示する。本文へ管理情報、CTA管理メモ、内部の確認事項を混ぜない。表示だけでは公開済みに変更しない。

## 8. 投稿済み管理

`X1投稿した https://...` または `note1投稿した https://...` を受けたら次を行う。

1. エイリアスを投稿IDへ解決する。
2. URLの媒体ホストと投稿IDのplatformが一致するか確認する。
3. 現在が `approved`、`editor_in_chief_passed`、`unpublished` であることをmainで再確認する。
4. `publishStatus: published`、`publishedAt: 現在のJST`、`publishedUrl: URL` へ更新する。
5. `state/PUB-ID-published` ブランチに対象レコードだけを変更する。
6. 状態専用PRを作り、差分がqueueの3項目だけであることを検査する。
7. 明示された「投稿した」を状態更新の承認として扱い、状態専用PRをmergeする。
8. 完了後、「記録しました」と投稿URLだけを返す。

状態更新の開始時に `mobile_post_state_update:canonicalId:publishedUrl` を重複キーとしてjobを登録し、merge完了後に `completed` とする。記事公開は `mobile_article_release:canonicalId:pullRequestUrl` を使用する。同じ対象・同じURLのcompleted jobがある場合は再実行しない。

同じURLの重複、すでにpublished、URL不一致、投稿時刻の逆転がある場合はmergeせず確認する。X・noteへの実投稿や削除は行わない。

## 9. 記事公開

`記事1公開` は外部公開を伴うため、次の全条件を満たす場合だけ実行する。

- 企画、原稿、公開実装がオーナー承認済み
- 対象PRと原稿IDの対応が一意
- PRがopenで、main向けである
- merge conflictがない
- 必須Checksが成功
- HTML、canonical、sitemap、CTA、管理マーカー検査が合格
- 公開URLが既存URLと重複しない
- stale lock、failed job、期限切れverifiedによる停止条件がない

処理順:

1. ChatGPTが対象タイトル、URL、PR、Checksを短く再表示する。
2. `記事1公開`を当該記事の最終公開指示として監査記録へ残す。
3. Draft PRをReady for reviewへ変更する。
4. Checksを再確認し、失敗・未完了ならmergeしない。
5. 自動マージを使わず、その場で対象PRだけをmergeする。
6. Cloudflareのmain連動デプロイ完了を確認する。
7. 公開URLのHTTP応答、title、canonical、主要CTAを確認する。
8. 状態専用PRでjob、原稿台帳、公開日時、公開URLを更新する。
9. ChatGPTへ公開URLと結果だけを返す。

Cloudflare失敗、Checks失敗、PR差分の変化、競合があれば `waiting_owner` で停止する。別記事、別PR、mainの他変更をまとめてmergeしない。

## 10. KPI

ChatGPTは `business/kpi/kpi-register.md` の定義と、GitHubに保存された最新の取得済みスナップショットを使用する。表示項目は次のとおり。

- 表示・インプレッション
- プロフィール表示
- リンククリック
- 問い合わせ
- 公開記事数
- X・note公開数

表示形式:

| KPI | 今日 | 今週 | 前週比 | 状態 | 最終取得 |
|---|---:|---:|---:|---|---|

取得元が未接続、期間が不明、値が古い場合は0にせず `未取得` と表示する。X、note、アクセス解析、問い合わせの認証情報はGitへ保存しない。初期運用ではオーナー入力または承認済み集計ファイルを使用し、将来コネクタを追加する場合も読み取り専用から始める。

## 11. GitHubを見せないための返答ルール

- 通常返答ではbranch、commit、PR番号、ファイルパスを表示しない。
- 成功時は「完了」「公開URL」「次の操作」だけを表示する。
- エラー時は原因と必要な判断だけを表示し、技術詳細は `詳細` で展開する。
- GitHubの変更履歴は監査用に保持し、ユーザーへGitHub操作を要求しない。
- 権限不足や競合でChatGPTが完了できない場合は、完了したように扱わない。

## 12. 権限と安全性

| 操作 | 必要権限 | 明示承認 |
|---|---|---|
| 朝会、X・note表示、KPI | GitHub read | 不要 |
| 承認・投稿済み状態更新 | Contents/PR write | コマンド自体で承認 |
| PR Ready化 | Pull requests write | `記事N公開` |
| PR merge | Pull requests/merge | `記事N公開` |
| Cloudflare結果確認 | Deployments read | `記事N公開` |
| X・note投稿 | 扱わない | オーナーが手動実行 |

mainへの直接push、複数PRの一括merge、自動マージ、未承認公開、X・note認証の保存は禁止する。書き込みは1操作1ブランチを原則とし、対象外ファイルが差分へ入った場合は停止する。

## 13. 導入手順

1. GitHub接続へmain読み取り、専用ブランチ作成、PR更新、mergeの必要最小限権限を設定する。
2. branch protectionと必須Checksを有効化する。
3. Cloudflareのmain連動デプロイとGitHub Deploymentsの参照可否を確認する。
4. 朝会データへ当日の固定エイリアスを生成する。
5. X表示、note表示、投稿済み状態更新をdry-runする。
6. 状態専用PRを1件テストし、対象項目以外が変わらないことを確認する。
7. 非公開テスト記事でReady化、merge、デプロイ確認を一度実施する。
8. KPIは取得元ごとに接続状態と更新時刻を表示する。
9. すべて合格後、ChatGPTを唯一の操作画面として案内する。

現状のGitHub正本だけで、朝会、X・note原稿表示、公開済み状態の管理、公開記事数は実現できる。プロフィール表示、クリック、問い合わせの自動集計には各取得元の読み取り連携またはオーナー入力が別途必要である。
