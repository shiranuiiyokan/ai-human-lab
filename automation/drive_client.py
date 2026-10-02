import io
import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]

def drive_credentials():
    raw = os.environ["AIHUMAN_GOOGLE_SERVICE_ACCOUNT_JSON"]
    info = json.loads(raw)
    return service_account.Credentials.from_service_account_info(info, scopes=DRIVE_SCOPES)

def build_drive_service():
    return build("drive", "v3", credentials=drive_credentials(), cache_discovery=False)

def list_children(service, folder_id):
    q = f"'{folder_id}' in parents and trashed=false"
    result = []
    token = None
    while True:
        r = service.files().list(
            q=q, pageSize=100, pageToken=token,
            fields="nextPageToken,files(id,name,mimeType,createdTime,size)",
            orderBy="createdTime",
        ).execute()
        result.extend(r.get("files", []))
        token = r.get("nextPageToken")
        if not token:
            return result

def list_child_folders(service, folder_id, limit=20):
    return [x for x in list_children(service, folder_id) if x["mimeType"] == "application/vnd.google-apps.folder"][:limit]

def download_file(service, file_id, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    req = service.files().get_media(fileId=file_id)
    with destination.open("wb") as f:
        dl = MediaIoBaseDownload(f, req)
        done = False
        while not done:
            _, done = dl.next_chunk()
    return destination

def download_job_folder(service, folder_id, destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    for item in list_children(service, folder_id):
        if item["mimeType"] == "application/vnd.google-apps.folder":
            continue
        download_file(service, item["id"], destination / item["name"])
    return destination

def find_child(service, folder_id, name):
    safe = name.replace("'", "\\'")
    q = f"'{folder_id}' in parents and name='{safe}' and trashed=false"
    files = service.files().list(q=q, pageSize=10, fields="files(id,name,mimeType)").execute().get("files", [])
    return files[0] if files else None

def upsert_json(service, folder_id, filename, data):
    payload = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    media = MediaIoBaseUpload(io.BytesIO(payload), mimetype="application/json", resumable=False)
    existing = find_child(service, folder_id, filename)
    if existing:
        return service.files().update(fileId=existing["id"], media_body=media, fields="id,name").execute()
    return service.files().create(
        body={"name": filename, "parents": [folder_id]},
        media_body=media, fields="id,name"
    ).execute()

def move_folder(service, folder_id, old_parent_id, new_parent_id):
    service.files().update(
        fileId=folder_id, addParents=new_parent_id, removeParents=old_parent_id, fields="id,parents"
    ).execute()
