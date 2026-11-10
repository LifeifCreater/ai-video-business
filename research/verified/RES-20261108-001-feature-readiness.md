---
researchId: RES-20261108-001
planId: PLAN-20261108-001
status: verified
verifiedAt: 2026-11-09T02:09:00+09:00
recheckBy: 2026-12-08
---

# 生成AI動画の新機能を本番制作へ採用する前の提供状態・制約調査

## 調査目的

企画 `PLAN-20261108-001` の原稿で使う外部事実を、公式一次情報だけで確認する。確認対象は、発表済み機能がすべての契約・環境で即時かつ安定して使えるとは限らないこと、管理者設定や出力条件の確認が必要なこと。

## 確認結果

### Google Vids：画像からカスタムアバターを作成

- 公式公開日：2026-11-02
- 公式更新日：2026-11-03
- 確認日：2026-11-09
- 対象版・範囲：Google Workspace Updates記載の対象契約・段階的提供
- 確認内容：11月2日の公開後、11月3日付の追記でロールアウト一時停止、再開時期未定と明記された。
- 採用判断への示唆：発表済みでも、案件時点の提供状態を再確認する必要がある。
- 公式URL：https://workspaceupdates.googleblog.com/2026/11/upload-image-create-custom-avatar-google-vids.html
- 再確認期限：2026-12-08、および公開実装前

### Adobe Firefly：Generate videos using Runway

- 公式最終更新日：2026-10-28
- 確認日：2026-11-09
- 対象版・範囲：Adobe Firefly video editor（beta）でのRunway Gen-4.5
- 確認内容：生成時間は5秒・8秒・10秒、解像度は720p、アスペクト比は16:9固定と記載されている。
- 採用判断への示唆：使える／使えないだけでなく、尺・解像度・比率が納品条件に適合するか確認する必要がある。
- 公式URL：https://helpx.adobe.com/firefly/web/firefly-video-editor/generate-videos/generate-videos-using-runway.html
- 再確認期限：2026-12-08、および公開実装前

### Adobe：Kling・Seedanceへの管理者アクセス制御

- 公式公開日：2026-11-06
- 確認日：2026-11-09
- 対象版・範囲：対象となるTeams・Enterprise契約
- 確認内容：管理者が対象モデルへのアクセスを制御でき、既定状態は契約・条件により異なる旨が公式Community Managerから案内された。
- 採用判断への示唆：編集者の画面に機能が見えるかだけでなく、管理者設定と契約条件を確認する必要がある。
- 公式URL：https://community.adobe.com/t5/enterprise-teams-discussions/manage-access-to-kling-and-seedance-models-in-adobe-firefly/m-p/15594170
- 再確認期限：2026-12-08、および公開実装前

### Google Vids：Omni 1.2 Flash

- 公式公開日：2026-11-05
- 確認日：2026-11-09
- 対象版・範囲：Google Workspace Updates記載の対象契約・段階的提供
- 確認内容：ロールアウトに1〜3日を要し、生成できる動画は最長15秒と案内された。
- 採用判断への示唆：同じ日でもアカウントごとに提供差が生じうるため、検証環境と確認日時を記録する。
- 公式URL：https://workspaceupdates.googleblog.com/2026/11/create-video-clips-with-omni-1-2-flash-google-vids.html
- 再確認期限：2026-12-08、および公開実装前

## 原稿で使用できる範囲

- 「発表済み」「画面に表示される」「案件で安定利用できる」は別の確認事項である。
- 契約、地域、管理者設定、アカウント、段階的提供、尺・解像度・比率を確認する。
- 機能停止や条件不一致に備え、代替手段を構成確定前に決める。

## 使用禁止・留保

- 全ユーザーへの一般提供、品質、性能、価格、法的適合を断定しない。
- FRAMEPACTが各機能を採用済み、または案件で利用を保証するとは書かない。
- 公開実装時には各公式ページを再確認する。
