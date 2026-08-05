# リサーチ情報源台帳

## 目的

AI動画リサーチで使用した情報源を、URL単位で重複なく管理する。調査開始前に本台帳を検索し、同一URLがあれば既存の情報源IDを再利用する。URLの追跡パラメータやページ内アンカーを除いた正規URLを重複判定に使う。

## 登録ルール

1. 情報源IDは `SRC-0001` から連番で付け、削除・再利用しない。
2. 同一の正規URLは1行だけ登録し、再確認時は確認日と状態を更新する。
3. 同じ文書の言語違い・版違いは別URLなら別行にし、関連情報源IDを記録する。
4. 公開日が確認できない場合は `不明` とし、推測した日付を書かない。
5. URLへアクセスできなくなった場合も行を削除せず、状態を `アクセス不可` に更新する。
6. 規約、料金、製品仕様など変更されるページは、確認日と対象条件を必ず記録する。
7. 登録しただけでは内容を採用したことにならない。各調査記録で対象主張と信頼性を評価する。

## 情報源一覧

| 情報源ID | 正規URL | 発行主体 | ページ・資料名 | 種別 | 公開日・更新日 | 初回確認日 | 最終確認日 | 信頼性 | 鮮度 | 状態 | 使用した調査ID | 関連情報源ID | メモ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `SRC-0000` |  |  |  | `公式 / 行政・団体・研究 / 報道 / 専門家記事 / SNS・個人ブログ / その他` |  |  |  | `A / B / C / 採用不可` | `最新 / 要再確認 / 参考・過去情報` | `有効 / アクセス不可 / 置換 / archive` |  |  | 記入例。実情報源には使用しない |
| `SRC-0001` | https://blog.google/products/ads-commerce/google-ads-ai-transparency-labels/ | Google | Expanding AI transparency in ads | 公式発表 | 2026-07-09 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-002` |  | 広告AI表示。2026-09-03再確認 |
| `SRC-0002` | https://support.google.com/youtube/answer/14328491?hl=en | YouTube | Disclosing use of GenAI content | 公式ドキュメント | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-002` |  | 通常投稿の申告。広告規則とは分離 |
| `SRC-0003` | https://support.google.com/adspolicy/answer/10249050?hl=en | Google | YouTube and Discover Feed ad requirements | 公式ドキュメント | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-002` |  | 広告審査要件 |
| `SRC-0004` | https://about.fb.com/news/2025/02/gen-ai-transparency-metas-ads-products/ | Meta | Expanding GenAI Transparency for Meta’s Ads Products | 公式発表 | 2026-06-01更新 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-002` |  | Facebook/Instagram広告。地域差あり |
| `SRC-0005` | https://ads.tiktok.com/help/article/about-ad-disclaimers-in-tiktok-ads-manager | TikTok | About ad disclaimers in TikTok Ads Manager | 公式ドキュメント | 2025-09更新 | 2026-08-03 | 2026-08-03 | A | 要再確認 | 有効 | `RES-20260803-002` | `SRC-0006` | AI広告表示 |
| `SRC-0006` | https://ads.tiktok.com/help/article/tiktok-ads-policy-misleading-and-false-content | TikTok | Misleading and false content | 公式ポリシー | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-002` | `SRC-0005` | 未表示時の拒否・制限 |
| `SRC-0007` | https://business.x.com/en/help/ads-policies | X | X Advertising Policies | 公式ポリシー | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-002` | `SRC-0008` | 広告とXルールの関係 |
| `SRC-0008` | https://help.x.com/en/rules-and-policies/authenticity | X | Authenticity | 公式ポリシー | 2025-04 | 2026-08-03 | 2026-08-03 | A | 要再確認 | 有効 | `RES-20260803-002` | `SRC-0007` | 合成・加工メディア |
| `SRC-0009` | https://developers.openai.com/api/docs/guides/your-data#default-usage-policies-by-endpoint | OpenAI | Data controls in the OpenAI platform | 公式ドキュメント | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-003` |  | APIデータ管理。機能別条件あり |
| `SRC-0010` | https://workspace.google.com/terms/service-terms/ | Google | Google Workspace Service Specific Terms | 公式規約 | 2026-07-16 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-003` | `SRC-0012` | Forms/Sheets等の対象データ |
| `SRC-0011` | https://support.google.com/docs/answer/10952360?hl=en | Google | Autosave your response progress on a Google Form | 公式ドキュメント | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-003` |  | 回答者の下書き保存 |
| `SRC-0012` | https://workspace.google.com/terms/subprocessors.html | Google | Google Workspace Subprocessors | 公式規約 | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-003` | `SRC-0010` | 契約別に確認 |
| `SRC-0013` | https://support.google.com/youtube/answer/1722171?hl=en | YouTube | Recommended upload encoding settings | 公式ドキュメント | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-004` | `SRC-0014` | 通常動画の推奨仕様 |
| `SRC-0014` | https://support.google.com/youtube/answer/6375112 | YouTube | Video resolution and aspect ratios | 公式ドキュメント | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-004` | `SRC-0013` | 解像度・比率 |
| `SRC-0015` | https://support.google.com/youtube/answer/15424877?hl=en | YouTube | Understand three-minute YouTube Shorts | 公式ドキュメント | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-004` |  | Shorts分類条件 |
| `SRC-0016` | https://support.google.com/google-ads/answer/10147229?hl=en | Google Ads | Video action campaigns creative guidelines | 公式ドキュメント | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-004` |  | YouTube広告仕様例 |
| `SRC-0017` | https://ads.tiktok.com/help/article/global-app-bundle-video-ad-specifications?lang=en | TikTok | Global App Bundle video ad specifications | 公式ドキュメント | 2025-07更新 | 2026-08-03 | 2026-08-03 | A | 要再確認 | 有効 | `RES-20260803-004` |  | 配置限定の仕様 |
| `SRC-0018` | https://help.x.com/en/using-x/x-videos | X | How to share and watch videos on X | 公式ドキュメント | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-004` |  | 通常投稿仕様 |
| `SRC-0019` | https://business.x.com/en/help/campaign-setup/creative-ad-specifications | X | X Ads creative specs | 公式ドキュメント | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 最新 | 有効 | `RES-20260803-004` |  | 動画広告仕様 |
| `SRC-0020` | https://www.facebook.com/business/ads/facebook-instagram-reels-ads | Meta | Instagram & Facebook Reels Ads | 公式ドキュメント | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 要再確認 | 有効 | `RES-20260803-004` | `SRC-0021` | 詳細数値未取得 |
| `SRC-0021` | https://www.facebook.com/business/ads/video-ad-format | Meta | Video ads | 公式ドキュメント | 更新日不明 | 2026-08-03 | 2026-08-03 | A | 要再確認 | 有効 | `RES-20260803-004` | `SRC-0020` | 配置別Ads Guide要確認 |

## 重複確認ログ

同一URLや実質的に同じ資料を統合した場合に記録する。

| 確認日 | 入力URL | 採用した情報源ID | 判定 | メモ |
|---|---|---|---|---|
|  |  |  | `新規 / 既存を再利用 / 版違いで新規` |  |
