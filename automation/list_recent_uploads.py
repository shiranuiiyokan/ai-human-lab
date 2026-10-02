import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES=[
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]
creds=Credentials(
    token=None,
    refresh_token=os.environ["AIHUMAN_YOUTUBE_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["AIHUMAN_YOUTUBE_CLIENT_ID"],
    client_secret=os.environ["AIHUMAN_YOUTUBE_CLIENT_SECRET"],
    scopes=SCOPES,
)
yt=build("youtube","v3",credentials=creds,cache_discovery=False)
ch=yt.channels().list(part="id,contentDetails",mine=True).execute()["items"][0]
print("CHANNEL",ch["id"])
playlist=ch["contentDetails"]["relatedPlaylists"]["uploads"]
items=yt.playlistItems().list(part="snippet,contentDetails",playlistId=playlist,maxResults=10).execute().get("items",[])
for item in items:
    print("VIDEO", item["contentDetails"]["videoId"], "|", item["snippet"]["title"])

ids=[item["contentDetails"]["videoId"] for item in items]
if ids:
    details=yt.videos().list(part="status",id=",".join(ids)).execute().get("items",[])
    for v in details:
        print("STATUS",v["id"],"|",v.get("status",{}).get("privacyStatus"))
