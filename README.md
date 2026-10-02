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
- 日次素材制作は通常チャット側のScheduled Task（07:00 JST）。Workは調査・監査専用
- production workflowは `.github/runtime-trigger.txt` のmain更新で起動
- 23:00 JSTのScheduled Taskは結果同期のみ（制作・追加投稿なし）
- ペット側repoは変更しない

## 音声設計
Shortsも長尺も、scene単位で音声をぶつ切り生成しない。
原則として動画1本につき連続したナレーション音声を先に生成し、visual sceneをその音声上に割り当てる。
読み補正は全文ひらがな化せず、単語単位のpronunciation辞書を使う。

## Queue / 結果連携（2026-10-03）
人物CloudのSheets APIは未有効化。GitHubはDriveの結果journalを更新し、Scheduled Taskが人物側Google connectorでProduction_QueueとResult_Logを同期する。
各動画フォルダの `youtube_result.json` と `error.json` は必ず人物Googleアカウントで事前作成する。サービスアカウントには新規Driveファイルの保存quotaがないため、GitHubは既存ファイルの更新だけを行う。
`automation/result_journal.py` は毎時17分に実公開/予約状態と、公開後24時間/7日の再生数・高評価・コメント数のsnapshotを記録する。取得時刻、経過時間、遅延有無を保持。Analytics専用のCTR・視聴維持率等はOAuth権限未設定として扱う。
Queueは予約確認後 `scheduled`、実公開確認後 `published`。video_id=S列、エラー理由=T列。既存video_idを再アップロードしない。
