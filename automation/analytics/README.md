# 問い合わせの照合と国内アクセス計測

## 実装状態

- サイト21ページは共通の `framepact-analytics.js` を使用する。
- `contact_form_click` はGoogleフォームへのクリックのみ。実際の送信成功を表す `generate_lead` をブラウザのクリックから作らない。
- 料金ページとトップページ内の料金ダイアログは `pricing_view` で計測する。
- クリックには `source_page`, `landing_page`, `observed_referrer`, `contact_channel`, `click_time_utc`, `measurement_version` を付ける。
- `observed_referrer` はブラウザで観測した参照元の分類であり、GA4のセッション帰属を置き換えない。入口情報の保存はタブ単位で30分のページ間非活動後に更新。GA4セッションの厳密な再現ではない。
- 自分の除外設定は `/analytics-owner.html` でブラウザごとに行う。保存成功を確認し、他のタブを再読み込みする。新しい端末・プライベートブラウズ・保存データ削除後は再設定。過去の内部アクセスは消えない。
- 本番ドメイン以外ではGAタグを読み込まない。Googleフォーム単独の計測にはこの除外設定は伝わらない。

フォーム側の完了イベント、GA4上のイベント生成ルール、実際の受信記録との照合はまだ未検証。Apps Scriptの存在・実装は確認できていない。既存の `generate_lead` がクリックから派生していないかも確認が必要。

## 公開前に必要な確認

1. GA4管理画面で `generate_lead` の生成・変更ルールを確認する。
2. 問い合わせ用Googleフォームの回答処理、既存Apps Scriptがあればその編集URLを確認する。
3. 送信成功時だけ発火するよう実装を接続する。Googleフォームにはサイト側GA4のclient/session情報が自動で引き継がれるとはみなさない。
4. 連携方式が決まってから、受付ID・実際の送信時刻・問い合わせ窓口と、取得できたclient_id/session_idの対応を、認可された非公開の回答記録へ保存する。未取得IDは生成して埋めない。名前・メール・相談文をGA4に送らない。
5. Measurement Protocolを使う場合はAPI secretをサーバー側だけに保存し、時刻・セッションの制約と重複防止を検証する。デバッグ検証の成功やHTTP 2xxだけで本番記録成功とみなさない。
6. 実送信テストは宛先・テスト内容を指定して承認を得た後に実施する。クリック、成功、失敗、二重送信、内部テストを区別する。

これらが終わるまで「問い合わせ帰属を完全実装」「送信完了を検証済み」と扱わない。旧データに結合情報がない場合、過去の帰属は復元できない。

## データ再確認

`python3 automation/analytics/report.py --date YYYY-MM-DD` は読み取りクエリ定義だけを表示する。
`--execute` を指定するとGA4 Data APIを読む。既存の閲覧権限を持つOAuthアクセストークンをローカル環境変数 `GA4_ACCESS_TOKEN` に設定する。認証情報をチャット・コード・PRに貼らない。

日付省略時は日本時間の2日前。結果にはGA4のtimeZoneなど元メタデータを残す。当日・前日は暫定扱いにするが、2日前でも確定を保証しない。API認証未接続のため実データでの実行は未検証。定期実行は未設定であり、このスクリプト単独では自動起動しない。

- 国内の日別人数、訪問、PV、エンゲージメント
- 国内の参照元別訪問
- 国内の料金ページ閲覧
- 全世界のクリック／generate_leadの分単位時刻・参照元・国
- 国内に限定した同イベント

サーバーイベントの国が欠ける場合に問い合わせを取り落とさないよう、全世界と日本の両方を確認する。受信メールの配送時刻とイベント発生時刻は同一とは限らない。時刻の一致だけで人を特定しない。送信完了率には、発火条件を検証したgenerate_leadを使い、クリックとの合計を使わない。

実行結果は標準出力のみ。Publicリポジトリ・PR・CIログへの実データ保存は禁止。API失敗やページング不完全を0件に置き換えない。

## 計測の扱い

氏名・メール・相談内容、任意のURLクエリ／ハッシュ、外部の参照元パスは送信しない。参照元はoriginまで。URL内キャンペーンは既知のutm_sourceとutm_mediumの組だけを引き継ぎ、任意のutm_campaignや広告クリックIDは引き継がない。広告運用を始める場合は、承認済みキャンペーン命名・プライバシー要件を確認して別途拡張する。

GA4の探索で新しい任意パラメータを使う場合はイベントスコープのカスタムディメンション登録が必要。`click_time_utc` のような高カーディナリティ値は標準の集計軸に登録しない。通常は標準のイベント時刻を使う。既存GA4設定はこの変更では操作していない。

## 検証

```
node --test tests/analytics.test.cjs
python3 -m unittest discover -s automation/analytics -p 'test_*.py'
ruby scripts/check-site.rb
```

## 仕様の参照（2026-09-29確認）

- https://developers.google.com/tag-platform/security/guides/privacy
- https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference
- https://developers.google.com/analytics/devguides/collection/protocol/ga4/use-cases
- https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport
