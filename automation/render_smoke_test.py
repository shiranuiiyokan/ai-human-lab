import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from render_video import render
from youtube_upload import upload_video

ROOT=Path("render_smoke_work")
ROOT.mkdir(exist_ok=True)

def make_test_image(path: Path, idx: int):
    img=Image.new("RGB",(1080,1920),(235-idx*8,235-idx*6,235-idx*4))
    d=ImageDraw.Draw(img)
    d.rectangle((120,240,960,1680),outline=(60,60,60),width=8)
    d.text((160,320),f"AIHuman E2E scene {idx}",fill=(30,30,30))
    img.save(path)

scenes=[]
texts=[
    "今回は、AI人物研究の音声と映像の接続テストです。",
    "これまでのように、シーンごとに音声を細かく切るのではなく、一本のナレーションとして自然につなげます。",
    "映像だけを途中で切り替えることで、声のテンポやイントネーションをできるだけ崩さない構成にします。",
    "表示する文字は画像そのものには焼き込まず、レンダリング時に重ねます。",
    "このテストは非公開でアップロードし、人物研究チャンネル以外には投稿されないようチャンネルIDも照合します。",
    "問題なく通れば、次は実際のAI人物画像を使った一本目の制作テストへ進みます。"
]
overlays=["接続テスト","連続ナレーション","映像だけ切り替え","文字は後から重ねる","投稿先を照合","次は実画像テスト"]
for i,(n,o) in enumerate(zip(texts,overlays),1):
    name=f"scene_{i:02d}.png"
    make_test_image(ROOT/name,i)
    scenes.append({"image":name,"narration":n,"overlay_text":o})

job={
    "project_id":"AIHUMAN-E2E-VOICE-001",
    "format":"short",
    "subject_age_min":20,
    "variable_under_test":"continuous_narration_pipeline",
    "youtube":{
        "title":"AI人物研究 音声レンダリングE2Eテスト（非公開）",
        "description":"AI人物研究の連続ナレーション方式の接続確認用テストです。",
        "tags":["AI人物研究","E2Eテスト"],
        "category_id":"22",
        "made_for_kids":False,
        "contains_synthetic_media":True
    },
    "scenes":scenes
}

out=ROOT/"rendered.mp4"
render(job,ROOT,out)
result=upload_video(out,job)
print("RENDER_SMOKE_SUCCESS",json.dumps(result,ensure_ascii=False),flush=True)
