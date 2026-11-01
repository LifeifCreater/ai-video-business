# 問い合わせの照合と国内アクセス計測

## 実装状態

- サイト21ページは共通の `framepact-analytics.js` を使用する。
- `contact_form_click` はGoogleフォームへのクリックのみ。実際の送信成功を表す `generate_lead` をブラウザのクリックから作らない。
- 料金ページとトップページ内の料金ダイアログは `pricing_view` で計測する。ダイアログは実際に開いた時の `framepact:pricing-view` 通知だけで記録し、ボタンクリックと `/#price` の直接リンク・ハッシュ遷移を同じ経路で扱う。ボタンの汎用クリックとの二重計測はしない。
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
`--execute` を指定するとGA4 Data APIを読む。対象は既存のプロパティ `547125968`。認証は次の優先順位で選び、選択された認証が不正な場合は別の認証へ黙って切り替えず停止する。

1. `GA4_ACCESS_TOKEN`：既存の手動取得との互換用。トークン期限後は再設定が必要。
2. `GA4_SERVICE_ACCOUNT_JSON`：GA4専用のサービスアカウントを既に設定している場合。
3. `GSC_SERVICE_ACCOUNT_JSON`：既存Search Console監視と同じサービスアカウントを利用する場合。

サービスアカウント実行時は `python3 -m pip install -r automation/analytics/requirements.txt` で依存を入れる。JSONはメモリ内で読み、Google公式 `google-auth` で `analytics.readonly` scopeだけを要求する。短期アクセストークンの発行・更新をSDKに任せ、鍵やトークンをファイル化しない。GSC側の認証scope・定期処理・保存状態は変更しない。

同じサービスアカウントでも、対象GA4プロパティの閲覧者権限と、対応するGoogle CloudプロジェクトでのGoogle Analytics Data API有効化が必要。GSCの成功をGA4権限の証明にしない。権限の付与、API有効化、鍵の新規発行はこのスクリプトでは実行しない。認証情報をチャット・コード・PRに貼らない。

日付省略時は日本時間の2日前。結果にはGA4のtimeZoneなど元メタデータを残す。当日・前日は暫定扱いにするが、2日前でも確定を保証しない。下記の定期処理で認証と取得を検証する。コードの存在やテスト合格だけを、実APIでの成功の証拠にしない。

- 国内の日別人数、訪問、PV、エンゲージメント
- 国内の参照元別訪問
- 国内の料金ページ閲覧
- 全世界のクリック／generate_leadの分単位時刻・参照元・国
- 国内に限定した同イベント

サーバーイベントの国が欠ける場合に問い合わせを取り落とさないよう、全世界と日本の両方を確認する。受信メールの配送時刻とイベント発生時刻は同一とは限らない。時刻の一致だけで人を特定しない。送信完了率には、発火条件を検証したgenerate_leadを使い、クリックとの合計を使わない。

通常の `--execute` はローカルでのみ結果を標準出力へ出す。Publicリポジトリ・PR・CIログ・公開Actions artifactへの実データ保存は禁止。GitHub Actionsでは通常の出力を認証前に拒否し、次の安全な確認モードだけを使用する。API失敗やページング不完全を0件に置き換えない。

## 定期的な取得確認

`.github/workflows/ga4-monitor.yml` は毎日08:40 JST予定（GitHubの実行遅延あり）と、対象ファイルのmain反映時、mainでの手動実行時に動く。PRや任意のブランチでは認証情報を使って実行しない。

```sh
python3 automation/analytics/report.py --execute --status-only
```

このモードは既存5種類のレポートを読み、応答とページングを検証した後、集計データをメモリから破棄する。公開ログへ出すのは接続の成否・認証方式・対象日・確認日時・完了したレポート定義数・固定の失敗分類だけ。指標値、取得行数、参照元、イベント時刻、Googleのエラー本文、鍵、アクセストークンは出さない。

workflowは `contents: read` のみで動き、checkoutにGitHub認証を残さず、Secretは取得stepだけへ渡す。GA4専用Secretがなければ既存 `GSC_SERVICE_ACCOUNT_JSON` を利用する。401/403、レート制限、ネットワーク障害、壊れた応答、不完全なページングは失敗として終了し、「アクセス0」や「問い合わせ0」と表示しない。実接続の確認証跡は、このworkflowの対象commitの実行結果を参照する。

**この定期処理で確認できるのは、GA4認証と5種類のクエリを継続して実行できること。実データの蓄積、朝会への数値配信、SEO改善案の生成、サイトの自動変更は含まない。** 集計値の保存・配信を接続する場合は、認可された非公開の保存先と閲覧範囲を確認してから別途つなぐ。公開のSearch Console state branchやKPI台帳を保存先にしない。

既存クエリは問い合わせ照合用の定義を維持している。朝会の本番ホスト限定・直近7日対前7日KPIと同一の定義ではないため、そのまま朝会の本番KPIへ転用しない。フォーム送信完了の検証も、上記の未検証項目として残る。

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

### 認証・定期取得の参照（2026-11-01確認）

- https://developers.google.com/analytics/devguides/reporting/data/v1/quickstart
- https://developers.google.com/analytics/devguides/MCP
- https://google-auth.readthedocs.io/en/latest/reference/google.auth.transport.requests.html
