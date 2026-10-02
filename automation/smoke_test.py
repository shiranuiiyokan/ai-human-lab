import json
import os
import subprocess
from pathlib import Path

from drive_client import build_drive_service, list_children
from youtube_upload import upload_video


def main():
    if os.getenv("PROJECT_NAMESPACE") != "AIHUMAN":
        raise SystemExit("ABORT: wrong namespace")

    drive = build_drive_service()
    short_folder = os.environ["AIHUMAN_SHORT_FOLDER_ID"]
    items = list_children(drive, short_folder)
    print(json.dumps({
        "drive_read_ok": True,
        "short_folder_item_count": len(items),
    }, ensure_ascii=False), flush=True)

    output = Path("smoke_e2e.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=4:r=30",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-shortest",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(output),
    ], check=True)

    job = {
        "project_id": "AIHUMAN-E2E-SMOKE",
        "title": "AI人物研究 E2E接続テスト",
        "youtube": {
            "title": "AI人物研究 E2E接続テスト",
            "description": "AI人物研究の自動制作パイプライン接続確認用の非公開テスト動画です。",
            "tags": ["AI人物研究", "E2Eテスト"],
            "category_id": "22",
            "made_for_kids": False,
            "contains_synthetic_media": True
        }
    }

    result = upload_video(output, job)
    print("SMOKE_SUCCESS", json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
