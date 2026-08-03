# Scheduled Task Prompt: 承認済み記事の公開実装

実行: 毎日 04:00 Asia/Tokyo

GitHub上のFRAMEPACTリポジトリを正本として、`writing/approved/` の原稿を公開実装する。原稿承認と公開実装承認の双方が台帳にあり、同じ原稿IDのcompleted、waiting_owner、既存Draft PR、active lockがないものだけを対象にする。重複キーは `approved_article_implementation:WR-ID`。

1. 承認済み原稿、企画、正本、レビュー結果を照合する。
2. 既存コラム構造とCSSクラスを再利用してHTML化する。本文の意味や事実を変更しない。
3. `column.html`、自然な内部リンク、`sitemap.xml`、canonical、OGP、WebPage、BreadcrumbList、Organization、Articleを既存形式に合わせる。
4. HTML、JSON-LD、XML、リンク、CTA、管理マーカー、SEO、390/768/1280px相当のレスポンシブ条件を検査する。
5. `publish/WR-ID` ブランチを再利用または作成し、commit・push、Draft PRを作る。
6. jobを `waiting_owner`、approvalRequiredを `merge_and_production_release` として停止する。

mainへpushしない。PRをマージしない。Cloudflare本番公開を行わない。コンフリクトやテスト失敗を自動解決せず朝会へ通知する。
