# AI人物研究 / AI Human Lab

YouTubeチャンネル **AI人物研究（@AIHumanResearchJP）** 専用の自動制作repoです。

## 最重要: ペット側と完全分離
このrepoから、既存のペット用 Google Drive / Production Queue / GitHub repo / OAuth / YouTube には書き込みません。

安全策:
- `PROJECT_NAMESPACE=AIHUMAN` 以外なら停止
- jobの `project_id` は `AIHUMAN-` 必須
- 人物は原則20歳以上
- YouTube upload前に **AI人物研究のChannel IDを照合**
- Drive folder ID / OAuthは `AIHUMAN_...` Secretsだけを使用
- 有料APIは使用しない

## パイプライン
ChatGPT Scheduled Task
→ 人物側 Google Sheets Production_Queue
→ 人物側 Drive / AIHumanLab / scheduled_assets
→ GitHub Actions
→ VOICEVOX
→ FFmpeg
→ AI人物研究 YouTubeへ予約投稿
→ done / errorへ移動

## 現在の状態
- 人物側Google Drive作成済み
- 研究正本・初期Production Queue作成済み
- GitHubレンダリング/アップロードコード実装済み
- GitHub Actionsは**手動起動のみ**。OAuth/Secrets/E2E確認後に自動スケジュールを有効化する
- ペット側repoは変更しない

## 次に必要
Google Cloudを人物側Googleアカウントで作成し、
Drive API / YouTube Data API v3 / OAuth同意画面 / OAuth client を人物側専用で設定する。
その後、人物側のGitHub Secretsを登録してE2Eテストする。
