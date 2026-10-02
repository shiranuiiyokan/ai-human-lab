import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

def youtube_credentials():
    return Credentials(
        token=None,
        refresh_token=os.environ["AIHUMAN_YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["AIHUMAN_YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["AIHUMAN_YOUTUBE_CLIENT_SECRET"],
        scopes=YOUTUBE_SCOPES,
    )

def build_youtube_service():
    return build("youtube", "v3", credentials=youtube_credentials(), cache_discovery=False)

def verify_channel(youtube):
    expected = os.environ["AIHUMAN_EXPECTED_CHANNEL_ID"].strip()
    if not expected:
        raise RuntimeError("AIHUMAN_EXPECTED_CHANNEL_ID is empty")
    resp = youtube.channels().list(part="id,snippet", mine=True).execute()
    items = resp.get("items", [])
    if len(items) != 1:
        raise RuntimeError(f"Expected exactly one authenticated YouTube channel, got {len(items)}")
    actual = items[0]["id"]
    if actual != expected:
        raise RuntimeError(f"WRONG YOUTUBE CHANNEL: expected={expected} actual={actual}")
    return actual

def upload_video(video_path: Path, job: dict):
    youtube = build_youtube_service()
    channel_id = verify_channel(youtube)

    y = job.get("youtube", {})
    description = y.get("description", "").rstrip()
    credit = os.getenv("VOICEVOX_CREDIT", "音声: VOICEVOX:ずんだもん")
    if credit and credit not in description:
        description += ("\n\n" if description else "") + credit
    disclosure = "この動画にはAI生成の人物画像・映像が含まれます。"
    if disclosure not in description:
        description += ("\n\n" if description else "") + disclosure

    publish_at = y.get("publish_at")
    status = {
        "privacyStatus": "private",
        "selfDeclaredMadeForKids": False,
        "containsSyntheticMedia": True,
    }
    if publish_at:
        status["publishAt"] = publish_at

    body = {
        "snippet": {
            "title": (y.get("title") or job.get("title") or "AI人物研究")[:100],
            "description": description,
            "tags": y.get("tags", ["AI人物研究", "AI生成", "比較"]),
            "categoryId": str(y.get("category_id", "22")),
            "defaultLanguage": "ja",
        },
        "status": status,
    }
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        progress, response = req.next_chunk()
        if progress:
            print(f"YouTube upload: {int(progress.progress()*100)}%")
    return {
        "video_id": response["id"],
        "youtube_url": f"https://www.youtube.com/watch?v={response['id']}",
        "publish_at": publish_at,
        "verified_channel_id": channel_id,
    }
