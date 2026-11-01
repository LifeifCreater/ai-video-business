# RES-20261101-001：動画納品ファイルの仕様確認

- 対象企画: `PLAN-20261101-001`
- 対象原稿: `WR-20261101-001`
- 確認日: 2026-11-01
- 再確認期限: 2026-12-01、かつ本番公開前
- 判定: 下記のAdobe公式資料について本文を取得し、記載範囲を検証。Runwayの新機能・発表日は今回の公開候補本文に使用しない。
- 役割: 同一アシスタントによる調査・確認。独立した別エージェントの検証ではない。

## 採用する根拠

### S1：Adobe Media Encoder — Export settings reference

- URL: https://helpx.adobe.com/media-encoder/desktop/encoding-and-exporting/export-settings-reference.html
- 本文取得: 成功
- ページに表示された更新日: 2026-03-27
- 対象: Adobe Media Encoderの書き出し設定リファレンス。画面・設定項目は形式やコーデックによって異なる。
- 確認箇所: Export Settings / Video / Bitrate Settings / Audio / Multiplexer / Captions。
- 確認できた事実: ビットレートは1秒あたりのデータ量。設定項目はコーデック・形式に依存する。コンテナと映像・音声の設定、フレームサイズ、フレームレートなどは別項目として扱われる。
- 使用範囲: 原稿の基本用語と、解像度・拡張子だけで仕様を決めないという説明の根拠。
- 使用しないもの: 特定ビットレートの一律推奨、FRAMEPACTの対応形式・対応ソフト・品質保証。

### S2：Adobe Premiere — Export video and audio files

- URL: https://helpx.adobe.com/premiere/desktop/render-and-export/export-files/export-video-and-audio-files.html
- 本文取得: 成功
- ページに表示された更新日: 2026-04-01
- 対象: Adobe Premiereの完成シーケンス・音声の書き出し手順。
- 確認できた事実: 書き出し形式のほか、フレームサイズ・フレームレート・縦横比、音声のチャンネル・サンプルレート・ビットレートを納品要件に合わせて確認する手順が記載されている。
- 使用範囲: 納品仕様を複数項目で確認する説明。
- 使用しないもの: 全ソフトの互換性、一般的な必須値、プロジェクトファイル一式の納品保証。

## 再取得に差異があった情報（非採用）

- 元企画のRunway更新履歴: https://docs.dev.runwayml.com/api-details/api_changelog/
- 検索結果には2026-10-27のSeedance 2.0系bitrate追加に関する記述があった。一方、ページ本文の取得結果は2026-08-07以前の内容で、当該更新を本文中で再確認できなかった。
- https://docs.dev.runwayml.com/guides/professional-outputs/ は検索結果にMOV・bitrateの説明があったが、本文取得が失敗した。
- https://docs.dev.runwayml.com/assets/inputs/ も検索結果と取得本文に版の差があった。
- 判断: 検索結果だけで最新仕様・追加日・価格を確定しない。公開候補本文ではRunway、Seedance、MOV追加日、bitrate追加日、モデル別仕様を記載しない。取得差異が機能の不存在を意味するとは判断しない。
- YouTubeのアップロード推奨設定ページも本文取得が429で失敗したため、具体的な推奨値を採用しない。

## 正本との照合

- `business/framepact-service-facts.md` の承認済み範囲: 企業・法人・団体向け、人による編集・構成調整・テロップ・音声・色味・品質確認、公式サイト内の問い合わせ導線。
- 未承認の具体的な納品形式、対応ソフト、保存期間、権利・料金条件を追加しない。
- 主CTA: https://framepact.jp/corporate-ai-video.html

## 事実と提案の区別

4用途への整理、9項目の仕様表、架空の命名例、受け入れ6手順、相談用メモは実務上の提案。AdobeやFRAMEPACTが標準として義務付ける手順ではない。これらを制作実績・性能保証・契約条件に変換しない。

元企画の目的・読者・納品用途の区別・受け入れ設計・CTAは維持し、取得差異のあるニュースを除いた実務記事として原稿レビューへ進める。公開承認は別途必要。
