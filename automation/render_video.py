import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from voicevox import synthesize

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
]

def run(cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run([str(x) for x in cmd], check=True)

def font_path():
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return p
    raise RuntimeError("Noto CJK font not found")

def audio_duration(path: Path):
    out = subprocess.check_output([
        "ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(path)
    ], text=True).strip()
    return max(1.0, float(out))

def cover_resize(img: Image.Image, width: int, height: int):
    ratio = max(width / img.width, height / img.height)
    nw, nh = int(img.width * ratio), int(img.height * ratio)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw-width)//2, (nh-height)//2
    return img.crop((left, top, left+width, top+height))

def wrap_text(text, max_chars):
    text = (text or "").strip()
    if not text:
        return []
    lines=[]
    while text:
        lines.append(text[:max_chars])
        text=text[max_chars:]
    return lines[:3]

def make_frame(image_path: Path, output_path: Path, overlay_text: str, width: int, height: int):
    base = cover_resize(Image.open(image_path).convert("RGB"), width, height)
    lines = wrap_text(overlay_text, 15 if height > width else 28)
    if lines:
        draw = ImageDraw.Draw(base, "RGBA")
        size = 70 if height > width else 54
        font = ImageFont.truetype(font_path(), size)
        padding = 28
        line_h = int(size * 1.35)
        box_h = line_h * len(lines) + padding * 2
        y0 = height - box_h - (120 if height > width else 70)
        draw.rounded_rectangle((60, y0, width-60, y0+box_h), radius=28, fill=(0,0,0,150))
        for i,line in enumerate(lines):
            bbox = draw.textbbox((0,0), line, font=font)
            tw = bbox[2]-bbox[0]
            x=(width-tw)//2
            y=y0+padding+i*line_h
            draw.text((x,y), line, font=font, fill=(255,255,255,255))
    base.save(output_path, quality=94)

def render(job: dict, work_dir: Path, output_path: Path):
    fmt = (job.get("format") or "short").lower()
    if fmt == "long":
        width,height,speed=1920,1080,float(os.getenv("LONG_VOICE_SPEED","1.20"))
    else:
        width,height,speed=1080,1920,float(os.getenv("SHORTS_VOICE_SPEED","1.45"))

    scenes=job.get("scenes") or []
    if not scenes:
        raise ValueError("No scenes")

    with tempfile.TemporaryDirectory() as td_raw:
        td=Path(td_raw)
        clip_paths=[]
        for idx,sc in enumerate(scenes,1):
            image_path=work_dir / sc["image"]
            if not image_path.exists():
                raise FileNotFoundError(image_path)
            frame=td/f"frame_{idx:03d}.jpg"
            wav=td/f"audio_{idx:03d}.wav"
            clip=td/f"clip_{idx:03d}.mp4"
            make_frame(image_path,frame,sc.get("overlay_text",""),width,height)
            narration=(sc.get("narration") or "").strip()
            if narration:
                synthesize(narration,wav,speed)
                dur=audio_duration(wav)+0.30
                run(["ffmpeg","-y","-loop","1","-i",frame,"-i",wav,"-t",f"{dur:.3f}",
                     "-vf",f"scale={width}:{height},format=yuv420p","-r","30",
                     "-c:v","libx264","-preset","veryfast","-c:a","aac","-b:a","160k",
                     "-ar","48000","-shortest",clip])
            else:
                dur=float(sc.get("duration_seconds",3.0))
                run(["ffmpeg","-y","-loop","1","-i",frame,"-t",str(dur),
                     "-f","lavfi","-i","anullsrc=r=48000:cl=stereo",
                     "-vf",f"scale={width}:{height},format=yuv420p","-r","30",
                     "-c:v","libx264","-preset","veryfast","-c:a","aac","-b:a","160k",
                     "-shortest",clip])
            clip_paths.append(clip)

        concat=td/"concat.txt"
        concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in clip_paths),encoding="utf-8")
        run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat,
             "-c:v","libx264","-preset","veryfast","-c:a","aac","-b:a","160k",
             "-movflags","+faststart",output_path])
    return output_path
