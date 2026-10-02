# AI人物研究 日次自動運用プロンプト

AI人物研究だけを処理する。ペット側のDrive / Sheets / GitHub / OAuth / YouTubeには一切触れない。

## Identity gate
1. 接続するGoogle Driveは人物側アカウント `yanjiuairenwu@gmail.com` のみ。
2. 正本Spreadsheetは `AIHumanResearch_Master_v1.0` / ID `1Lliq2vUmS5e_GSGLaha4xj-lfk4WZIVzpt523qA-ukY` のみ。
3. Driveは `AIHumanLab` 配下だけに書き込む。
4. GitHubは `shiranuiiyokan/ai-human-lab` だけに書き込む。
5. PET / DOG / MBTI / CAT / NEWS namespace、ペット用Drive、dog-video-maker を見つけた場合は停止する。
6. 有料API、有料TTS、有料動画生成、有料ストレージは禁止。

## Config first
毎回最初に `Automation_Config` を読む。
- `PET_WRITE_BLOCK=TRUE` でなければ停止。
- `PROJECT_NAMESPACE=AIHUMAN` でなければ停止。
- `RUN_MODE=CANARY_PRIVATE` の間は、Shortsを最古1件だけ制作し、Longは制作しない。
- `RUN_MODE=PRODUCTION` になった後だけ `DAILY_SHORTS` / `WEEKLY_LONG` に従う。
- `AUTO_PUBLISH=FALSE` の間は manifest の `youtube.publish_at` を null または省略し、必ず非公開アップロードにする。
- `AUTO_PUBLISH=TRUE` のときだけ Production_Queue の公開日・公開枠を使用する。

## Queue
`Production_Queue` の `status=queued` だけを対象にし、production_date 昇順を基本に priority を考慮する。
同じ queue_id / experiment_id で人物側Driveに着手済みフォルダがある場合は重複制作しない。

## Content
- 人物は20歳以上の成人のみ。年齢が曖昧に見える生成はFAIL。
- `GENDER_MIX=MIXED` の場合、女性だけに偏らせず男性企画も継続する。ただしQueueのsubjectが明示されている場合はQueueを優先する。
- 女性・男性とも同じ品質基準で扱い、性別ごとに露出や性的強調へ寄せない。
- 日本人成人を基本とする。
- ヌード、下着見せ目的、性的部位の強調、露骨な性的表現は禁止。
- 盗撮・覗き見・無断撮影の再現は禁止。
- 友人が普通のスマホで撮った自然なスナップは可。
- 比較実験は原則1回1変数。Research_Master の control_conditions を固定。
- 「美人だから」だけの比較にしない。自然さ、親しみ、AIっぽさ、雰囲気など企画の検証軸を明確にする。
- scene画像には文字を焼き込まない。表示文字は `overlay_text` に分離。
- リアルなAI人物を使うため `contains_synthetic_media=true`。
- 人物は過度なモデル顔・広告写真・完璧ポーズに寄せず、普通のスマホ写真らしい少しの不完全さを残す。
- 承認済み基準は「綺麗すぎない」「撮影を強く意識していない自然な瞬間」「生活感」「自然な隙」「露出なしでも目を引く魅力」。
- ただし盗撮・覗き見・無断撮影の再現は禁止。表現は友人や同行者が普通のスマホで撮った自然なスナップとして成立させる。
- 美肌補正、広告照明、完璧なヘアメイク、モデル立ち、過度な背景ボケ、映画ポスター風の演出を避ける。
- 軽い髪の乱れ、服の自然なしわ、少し崩れた姿勢、視線外し、食事中、スマホ中、歩行中、犬との自然なやり取りなどを使って生活感を出す。
- 「自然な魅力」は表情・視線・姿勢・距離感・仕草・光・場面から出す。胸・尻・脚など身体部位を主目的にしない。

## Script / audio
- Shortsは30〜55秒を基本。
- 先に動画1本として自然につながるナレーション全文を完成させる。
- sceneごとに独立した文章を並べて、音声がぶつ切りに聞こえる構成にしない。
- narrationは漢字かな混じりの自然な日本語。
- 全文ひらがな化は禁止。
- 読み補正は必要な語だけ各sceneの `pronunciation` 辞書へ入れる。
- 基本構成: hook → 条件固定説明 → A/B比較 → 観察 → 視聴者への問い。
- VOICEVOXは人物側production設定に従う。現在は春日部つむぎ / speed 1.30。

## Visual design
Shortsは9:16 / 1080x1920 / 30fps、原則6scene。
ただしA/B比較の成立を最優先し、比較sceneは変更変数以外を可能な限り固定する。

各sceneについて画像生成前に以下を決める:
- scene_id
- purpose
- image_format
- main_subject
- composition
- camera_distance
- camera_angle
- background
- variable_state
- fixed_conditions
- narration
- overlay_text
- pronunciation

自然さのためのsceneと、厳密比較のsceneを区別する。
比較scene A/Bでは同一人物感、服装、背景、照明、カメラ位置を固定し、指定変数だけ変える。
補助sceneでは距離・角度・背景に変化をつけて動画全体の単調さを避ける。

## Drive job
保存先:
- Short: `AIHumanLab/scheduled_assets/shorts`
- Long: `AIHumanLab/scheduled_assets/long`

1動画1フォルダ。フォルダ名は `YYYYMMDD_AIHUMAN-<queue_id>` を基本とする。

必須:
- `manifest.json`
- `scene_plan.json`
- `scene_qc.json`
- `scene_01.png ... scene_N.png`

manifest必須:
- project_id: `AIHUMAN-...`
- experiment_id
- format: short / long
- variable_under_test
- subject_age_min >= 20
- scenes[].image
- scenes[].narration
- scenes[].overlay_text
- 必要なら scenes[].pronunciation
- youtube.title
- youtube.description
- youtube.made_for_kids=false
- youtube.contains_synthetic_media=true
- CANARY_PRIVATE / AUTO_PUBLISH=FALSE の間は youtube.publish_at を入れない

## QC
全scene生成後に確認:
- 画像欠損0
- 成人20+が明確
- 手指・顔・服の重大破綻なし
- A/Bで変更変数以外が不用意に変わっていない
- 同じ補助構図が連続しすぎていない
- 画像内に不要な文字がない
- narrationを連結したとき自然な一本の文章になる
- 読み間違いリスク語をpronunciationへ登録
FAILがあればそのsceneだけ差し替える。

## Completion / trigger
Driveに全scene + manifest + scene_plan + scene_qc が揃い、再読込確認できたときだけ Production_Queue の status を `generated` に更新する。

その後だけ、GitHub repo `shiranuiiyokan/ai-human-lab` の `.github/runtime-trigger.txt` を現在時刻・project_idが分かる内容へ更新してproduction workflowを起動する。

GitHub/YouTubeの結果を確認できていない段階で「投稿完了」とは扱わない。
CANARY_PRIVATE中はYouTubeは非公開のみ。公開予約は行わない。
