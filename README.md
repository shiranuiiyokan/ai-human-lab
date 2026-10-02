# AI人物研究 / AI Human Lab

YouTubeチャンネル **AI人物研究（@AIHumanResearchJP）** 専用の自動制作repoです。

## 最重要: ペット側と完全分離
このrepoから、既存のペット用 Google Drive / Production Queue / GitHub repo / OAuth / YouTube には書き込みません。

安全策:
- `PROJECT_NAMESPACE=AIHUMAN` 以外なら停止
- jobの `project_id` は `AIHUMAN-` 必須
- 人物は原則20歳以上
- YouTube upload前に **AI人物研究のChannel IDを照合**
- Driveは人物側サービスアカウント、YouTubeは人物側OAuthのみ使用
- 秘密情報は `AIHUMAN_...` GitHub Secretsのみ
- 有料APIは使用しない

## パイプライン
ChatGPT Scheduled Task
→ 人物側 Google Sheets Production_Queue
→ 人物側 Drive / AIHumanLab / scheduled_assets
→ GitHub Actions
→ VOICEVOX
→ FFmpeg
→ AI人物研究 YouTube
→ done / errorへ移動

## 現在の状態
- 人物側Google Drive / 研究正本 / Production Queue 作成済み
- GitHubレンダリング/アップロードコード実装済み
- Driveサービスアカウント疎通: PASS
- YouTube OAuth / チャンネルID照合 / 非公開アップロード: PASS
- Google Auth Platform: 本番環境へ移行済み
- 本番環境移行後のRefresh token取り直しだけ保留（PC利用時に実施）
- 通常のproduction workflowは手動起動のまま
- ペット側repoは変更しない

## 音声設計
Shortsも長尺も、scene単位で音声をぶつ切り生成しない。
原則として動画1本につき連続したナレーション音声を先に生成し、visual sceneをその音声上に割り当てる。
読み補正は全文ひらがな化せず、単語単位のpronunciation辞書を使う。
