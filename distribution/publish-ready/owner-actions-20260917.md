# 投稿・企画状態の修復記録（2026-09-17）

## 公開済みとして確定

- `PUB-NOTE-001`、`PUB-NOTE-002`、`PUB-NOTE-003`
  - note.com/framepactの本文一致と公開URLを確認
  - 表示時刻のタイムゾーンは未確定のため、`publishedAt`は推測せず未取得
- `PUB-X-004`
  - 公開検索による本文一致確認を維持
  - 個別投稿URLと正確な公開時刻は未取得

## 未公開候補

- `publishStatus: unpublished`の投稿に公開日時を自動設定していない
- `ownerDecisionRecommendation: reject`は重複保留として分類
- その他の承認済み候補は`ownerScheduleRequired: true`とし、投稿時刻はオーナー判断事項
- 自動投稿、予約投稿、公開済みへの推測変更は行っていない

## 企画承認

1. `PLAN-20260913-001`を優先順位1で承認
2. `PLAN-20260913-002`を優先順位2で承認

いずれも公開承認とは別で、夜間制作はレビュー用Draft PRまでで停止する。
