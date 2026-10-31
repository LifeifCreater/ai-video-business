# PR #79 Google Vids機能説明の事実確認

- 調査ID: RES-20261030-PR79
- 対象: WR-20261025-001 / WR-20261025-002
- 確認日: 2026-10-30（日本時間）
- 状態: verified・有効（下記の主張と出典の対応に限定）
- 再確認期限: 2026-11-25。公開工程に入る時点、仕様変更が判明した時点にも再確認
- 対象版: Google Vids、2026-10-23付の各機能発表と確認日現在のヘルプ
- 担当: 同一アシスタントによる一次情報照合。独立レビュー・実機検証は未実施
- 公開・原稿・企画承認: 未承認。調査合格は承認を代替しない

## 出典

| ID | 一次情報 | 公開日 | 確認日 |
|---|---|---|---|
| S1 | [Adjust video clip playback speed directly in Google Vids](https://workspaceupdates.googleblog.com/2026/10/adjust-video-clip-playback-speed-directly-in-Google-Vids.html) | 2026-10-23 | 2026-10-30 |
| S2 | [Extract audio tracks in Google Vids](https://workspaceupdates.googleblog.com/2026/10/extract-audio-tracks-in-google-vids.html) | 2026-10-23 | 2026-10-30 |
| H1 | [Edit a video clip on Google Vids](https://support.google.com/docs/answer/18735545?hl=en) | ページに公開日表記なし | 2026-10-30 |
| H2 | [Control audio timing, balance & transitions with audio tracks](https://support.google.com/docs/answer/14999865?hl=en) | ページに公開日表記なし | 2026-10-30 |
| H3 | [Add audio to a video in Google Vids](https://support.google.com/docs/answer/15001100) | ページに公開日表記なし | 2026-10-30 |

## 主張の照合

| 主張 | 根拠 | 判定・原稿への処置 |
|---|---|---|
| 制作中の個別クリップの速度を最小0.25倍・最大2倍に変更 | S1のKey capabilities、H1の速度・長さ調整 | 確認済み。視聴プレーヤーの倍速操作と区別 |
| 速度変更の展開は10/16から最長15日、音声抽出は10/19から最長15日 | S1/S2のRollout pace | 確認済み。10/23の発表日と区別 |
| 両機能の対象は全Workspace顧客、Individual契約者、個人Googleアカウント | S1/S2のAvailability | 確認済み。全アカウントへの展開完了や、Vidsの全機能の無条件利用までは断定しない |
| 音声を独立クリップ化し、元映像と別にトリミング・移動・削除、複数シーンで使用 | S2の本文・Key capabilities、H2 | 確認済み。音声ファイルのダウンロード機能と区別 |
| 速度変更で音声ピッチが保たれ、字幕が自動追従する | S1/H1に詳細記載なし | 未確認。保証せず、素材で確認する項目に変更 |
| 抽出だけでAI話者分離・自動ノイズ除去が行われる | S2の具体的機能にその処理の説明なし | 裏付けなし。そう読める表現を排除。S2の背景雑音への言及は、自動処理の仕様とは解釈しない |
| MP3/WAVでの単体出力、無劣化性、再圧縮、抽出直後の元音声の状態、自動同期 | S2/H2/H3では本稿に必要な保証を確認できず | 未確認。H3の入力可能形式を出力仕様に流用しない。元動画を保存基準とし、実際の再生結果で確認 |
| 学習効果・視聴維持率の改善 | 効果量や検証条件の根拠なし | 成果として記載しない |
| FRAMEPACTでのGoogle Vids採用・公式提携 | 根拠なし | 記載しない |

「未確認」は機能が存在しないという断定ではない。操作手順の詳細を増やす場合は、追加の一次情報と実機確認が必要。

## 事実と編集提案の境界

変更区間の記録、元動画と配置先の対応表、口元・動作・字幕の照合、確認者の割当は、本レビューで整えた編集実務上の提案。Googleが定めた承認基準とはしない。

WR-001の12秒÷1.5＝8秒は速度だけを変更する架空の算術例。推奨倍率、実案件実績、効果の測定値ではない。WR-002の時刻・IDも架空の記入例。

## FRAMEPACTの情報

`business/framepact-service-facts.md`のmainとPRブランチが同一blob（e09e27ec4bad2db5fdc5c2e8bf9e52877def014d）であることを確認。対象顧客、研修・教育動画／イベント動画、人による編集・構成調整・音声・品質確認の承認済み表現だけを使用。新しい価格、納期、採用ツール、顧客実績は追加しない。
