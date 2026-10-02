# AI人物研究 日次自動運用プロンプト

AI人物研究だけを処理する。ペット側のDrive / Sheets / GitHub / OAuth / YouTubeには一切触れない。

## Identity gate
1. 接続するGoogle Driveは「AI人物研究」アカウントのみ。
2. Driveユーザーが人物側アカウントであることを確認してから書き込む。
3. AIHumanLab 配下以外へ人物素材を書き込まない。
4. PET / DOG / MBTI / CAT / NEWS namespaceを見つけた場合は停止する。

## Queue
人物側 Google Sheets「AIHumanResearch_Master_v1.0」の Production_Queue だけを正本とする。
status=queued かつ production_date<=翌日の対象から、Shortを最大2件。
週次Longは、その週の結果が十分ある場合のみ最大1件。

## Content
- 人物は原則20歳以上の日本人成人。
- 未成年を生成しない。
- ヌード、下着見せ目的、性的部位の強調、露骨な性的表現は使わない。
- 盗撮・覗き見・無断撮影の再現はしない。
- 「友人が普通のスマホで撮った自然なスナップ」は可。
- 比較実験は原則1回1変数。他条件を固定。
- 人物の美しさより、普通っぽさ、生活感、少しの不完全さ、自然な姿勢を優先。
- scene画像には文字を焼き込まない。表示文字は overlay_text に分離。
- リアルなAI人物を使うため manifest の contains_synthetic_media=true。
- 有料API、有料TTS、有料動画生成、有料ストレージは禁止。

## Short format
- 9:16 / 1080x1920 / 30fps
- 5〜8 scenes
- 30〜55秒
- 構成: hook → 条件A → 条件B → 観察 → コメント参加
- 同じ距離・姿勢・背景を連続させない。ただしA/B比較sceneは比較条件以外を固定。

## Job folder
scheduled_assets/shorts または scheduled_assets/long の直下に1動画1フォルダを作る。

必須:
- manifest.json
- scene_01.png ... scene_N.png

manifestには以下を必ず入れる:
- project_id: AIHUMAN-...
- experiment_id
- format: short / long
- variable_under_test
- subject_age_min >= 20
- scenes[].image
- scenes[].narration
- scenes[].overlay_text
- youtube.title
- youtube.description
- youtube.publish_at
- youtube.made_for_kids=false
- youtube.contains_synthetic_media=true

生成後、Production_Queue の status を generated に更新する。
