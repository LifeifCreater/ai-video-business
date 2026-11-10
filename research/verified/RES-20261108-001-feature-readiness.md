---
researchId: RES-20261108-001
planId: PLAN-20261108-001
status: verified
verifiedAt: 2026-11-10T09:52:37+09:00
recheckBy: 2026-12-08
---

# 生成AI動画の新機能を本番制作へ採用する前の提供状態・制約調査

## 調査目的

企画 `PLAN-20261108-001` の外部事実を公式一次情報で確認する。発表済み機能がすべての契約・環境で即時かつ安定して使えるとは限らないこと、管理者設定や出力条件の確認が必要なことを対象とする。

## 公開前の再確認（2026-11-10）

以前の記録にあった公式URL4件は、この実装時の取得で本文を読めなかった。公式ドメインに限定した検索で実在する参照先と本文を再取得し、以下へ修正した。Google2件・Adobe Community1件は公式ページの検索取得本文、Adobe Helpはページ本文でも記載内容を確認した。各契約アカウントでの実機検証はしていない。

Adobe Helpの最終更新日は検索取得とページ取得で表示が異なったため、公開原稿では更新日を断定せず、今回の確認日と対象機能を記載する。仕様の数値自体は両方で一致した。

## 確認結果

### Google Vids：画像からカスタムアバターを作成

- 公式公開日：2026-11-02
- 提供停止に関する追記：2026-11-03
- 確認日：2026-11-10
- 対象：Google Workspace Updates記載の対象契約・段階的提供
- 確認内容：11月3日の追記でロールアウト一時停止、再開時期未定と記載。
- 示唆：発表済みでも案件時点の提供状態を再確認する。
- 公式URL：https://workspaceupdates.googleblog.com/2026/11/create-a-custom-avatar-google-vids.html?hl=en

### Adobe Firefly：Generate videos using Runway video generation models

- 確認日：2026-11-10
- 対象：Adobe Firefly内の動画編集機能で使うRunway Gen-4.5
- 確認内容：生成時間5秒・8秒・10秒、解像度720p、アスペクト比16:9固定。
- 示唆：尺・解像度・比率を納品条件と照合する。
- 留保：Runwayサービス全体の仕様へ一般化しない。公式ページの表示更新日は取得方法で異なったため断定しない。
- 公式URL：https://helpx.adobe.com/firefly/web/firefly-video-editor/generate-videos/generate-videos-using-runway-video-models.html

### Adobe：Kling・Seedanceへの管理者アクセス制御

- 公式公開日：2026-11-06
- 確認日：2026-11-10
- 対象：対象となるCreative Cloud Teams・Enterprise契約
- 確認内容：Community Managerの案内で、管理者がモデルへのアクセスを制御でき、既定状態が契約条件によって異なると記載。
- 示唆：個人画面だけでなく組織アカウントと管理者設定を確認する。
- 公式URL：https://community.adobe.com/announcements-623/manage-access-to-kling-and-seedance-partner-models-for-creative-cloud-teams-and-enterprise-1654590

### Google Vids：Gemini Omni 1.2 Flash

- 公式公開日：2026-11-05
- 確認日：2026-11-10
- 対象：Google Workspace Updates記載の対象契約・段階的提供
- 確認内容：動画は最長15秒。11月5日から機能表示まで1〜3日を要する提供案内。
- 示唆：検証環境と確認日時を記録する。個別アカウントでの表示・利用を保証しない。
- 公式URL：https://workspaceupdates.googleblog.com/2026/11/gemini-omni-12-flash-now-in-vids-with-15second-generations-and-improved-quality.html?m=0

## 原稿で使用できる範囲

- 「発表済み」「画面に表示される」「案件で安定利用できる」は別の確認事項である。
- 契約、地域、管理者設定、アカウント、段階的提供、尺・解像度・比率を確認する。
- 機能停止や条件不一致に備え、代替手段を構成確定前に決める。

## 使用禁止・留保

- 全ユーザーへの一般提供、品質、性能、価格、法的適合を断定しない。
- FRAMEPACTが各機能を採用済み、案件での利用を保証する、または実機検証済みとは書かない。
- 公開記事には2026-11-10の情報確認時点であることと、案件採用時の再確認が必要であることを記載する。
- 再確認期限は2026-12-08。仕様変更や提供状態の変更を認識した場合は期限前でも再確認する。
