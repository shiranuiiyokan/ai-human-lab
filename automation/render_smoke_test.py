import json
from pathlib import Path
from PIL import Image, ImageDraw

from render_video import render
from youtube_upload import upload_video

ROOT=Path("render_smoke_work")
ROOT.mkdir(exist_ok=True)

W,H=1080,1920

def draw_room(img):
    d=ImageDraw.Draw(img)
    d.rectangle((0,0,W,H), fill=(239,236,229))
    d.rectangle((80,180,1000,1740), fill=(248,247,243))
    d.rectangle((120,240,470,850), fill=(220,231,236))
    d.rectangle((135,255,455,835), fill=(229,239,244))
    d.line((295,255,295,835), fill=(195,208,214), width=5)
    d.line((135,545,455,545), fill=(195,208,214), width=5)
    d.rectangle((670,400,940,1050), fill=(226,214,198))
    d.rectangle((705,455,905,520), fill=(246,244,236))
    d.ellipse((760,320,850,410), fill=(126,151,119))
    d.rectangle((0,1500,W,H), fill=(213,198,181))
    d.rectangle((0,1450,W,1505), fill=(193,175,156))

def draw_woman(path: Path, pose: str):
    img=Image.new("RGB",(W,H),(239,236,229))
    draw_room(img)
    d=ImageDraw.Draw(img)

    # fixed subject anchor
    cx=555
    head_y=560
    skin=(232,195,172)
    hair=(59,49,44)
    top=(226,215,197)
    jeans=(92,116,142)

    # posture-specific torso geometry
    if pose=="upright":
        neck=(cx,730); shoulder_y=760; hip=(cx,1120); lean=0
    elif pose=="relaxed":
        neck=(cx-12,735); shoulder_y=770; hip=(cx+15,1125); lean=18
    elif pose=="slouch":
        neck=(cx-35,750); shoulder_y=790; hip=(cx+45,1135); lean=40
    elif pose=="open":
        neck=(cx,725); shoulder_y=750; hip=(cx,1115); lean=-8
    elif pose=="gentle":
        neck=(cx-18,738); shoulder_y=775; hip=(cx+22,1128); lean=22
    else:
        neck=(cx,735); shoulder_y=770; hip=(cx,1125); lean=8

    # head/hair
    d.ellipse((cx-120,head_y-120,cx+120,head_y+120), fill=skin)
    d.pieslice((cx-135,head_y-145,cx+135,head_y+105),180,360,fill=hair)
    d.ellipse((cx-118,head_y-130,cx+118,head_y+30), fill=hair)
    d.polygon([(cx-110,head_y-40),(cx-75,head_y+95),(cx-120,head_y+115)], fill=hair)
    d.polygon([(cx+110,head_y-40),(cx+70,head_y+100),(cx+120,head_y+115)], fill=hair)
    d.ellipse((cx-52,head_y-2,cx-36,head_y+12), fill=(65,54,50))
    d.ellipse((cx+36,head_y-2,cx+52,head_y+12), fill=(65,54,50))
    d.arc((cx-36,head_y+30,cx+36,head_y+70),0,180,fill=(149,92,84),width=4)

    # torso polygon varies only by posture
    sx1=cx-145+lean; sx2=cx+145+lean
    hy=hip[1]
    d.polygon([(sx1,shoulder_y),(sx2,shoulder_y),(cx+105+lean,hy),(cx-105+lean,hy)], fill=top)

    # arms
    if pose=="open":
        d.line((sx1+15,shoulder_y+30,cx-250,980), fill=skin, width=52)
        d.line((sx2-15,shoulder_y+30,cx+250,980), fill=skin, width=52)
    elif pose=="slouch":
        d.line((sx1+20,shoulder_y+35,cx-150,1035), fill=skin, width=52)
        d.line((sx2-20,shoulder_y+35,cx+120,1045), fill=skin, width=52)
    else:
        d.line((sx1+20,shoulder_y+35,cx-165+lean,1010), fill=skin, width=52)
        d.line((sx2-20,shoulder_y+35,cx+165+lean,1010), fill=skin, width=52)

    # legs
    d.polygon([(cx-102+lean,hy-5),(cx-8+lean,hy-5),(cx-55+lean,1515),(cx-155+lean,1515)], fill=jeans)
    d.polygon([(cx+8+lean,hy-5),(cx+102+lean,hy-5),(cx+155+lean,1515),(cx+55+lean,1515)], fill=jeans)
    d.ellipse((cx-185+lean,1490,cx-35+lean,1545), fill=(245,245,242))
    d.ellipse((cx+35+lean,1490,cx+185+lean,1545), fill=(245,245,242))

    # subtle smartphone imperfection
    d.ellipse((65,1180,120,1235), fill=(194,204,188))
    d.ellipse((940,1280,985,1325), fill=(205,197,184))
    img.save(path)

poses=["neutral","upright","relaxed","slouch","open","gentle"]
for i,p in enumerate(poses,1):
    draw_woman(ROOT/f"scene_{i:02d}.png",p)

texts=[
    "同じ人でも、姿勢だけで印象は変わるのか。今回は、服も髪も場所も光も同じにして、姿勢だけを変えて比べます。",
    "まずは背筋をまっすぐ伸ばした姿勢。きちんとして見えやすい一方で、少しだけ緊張感も出やすいです。",
    "次は肩の力を少し抜いた姿勢。顔や服は同じでも、距離が近く感じるような、やわらかい印象が出ます。",
    "さらに少し前に重心を置くと、自然さは増える反面、だらしなく見える境目にも近づきます。",
    "逆に胸を開いて立つと、自信があるようには見えますが、日常のスマホ写真としては少し作った感じも出ます。",
    "結局、姿勢だけでも印象はかなり動きます。あなたなら、まっすぐと少し力を抜いた姿勢、どっちが自然に見えますか。"
]
overlays=["姿勢だけ変えます","A まっすぐ","B 少し力を抜く","C 前重心","D 胸を開く","どれが自然？"]

scenes=[]
for i,(n,o) in enumerate(zip(texts,overlays),1):
    scenes.append({
        "image":f"scene_{i:02d}.png",
        "narration":n,
        "overlay_text":o
    })

job={
    "project_id":"AIHUMAN-HR001-CANARY-001",
    "experiment_id":"HR-001",
    "format":"short",
    "subject_age_min":27,
    "variable_under_test":"posture",
    "youtube":{
        "title":"姿勢だけで印象は変わる？｜AI人物研究",
        "description":"同じ人物・同じ服・同じ場所で、姿勢だけを変えた比較テストです。今回は自動制作パイプラインの初回カナリアとして非公開アップロードします。",
        "tags":["AI人物研究","AI生成","姿勢","比較"],
        "category_id":"22",
        "made_for_kids":False,
        "contains_synthetic_media":True
    },
    "scenes":scenes
}

out=ROOT/"rendered.mp4"
render(job,ROOT,out)
result=upload_video(out,job)
print("CANARY_SUCCESS",json.dumps(result,ensure_ascii=False),flush=True)
