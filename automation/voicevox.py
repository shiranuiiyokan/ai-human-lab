import os
from pathlib import Path
import requests

BASE_URL = os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")

def wait_until_ready(timeout=180):
    r = requests.get(f"{BASE_URL}/version", timeout=timeout)
    r.raise_for_status()
    return r.text

def resolve_speaker_id():
    explicit = os.getenv("VOICEVOX_SPEAKER_ID")
    if explicit:
        return int(explicit)
    name = os.getenv("VOICEVOX_SPEAKER_NAME", "ずんだもん")
    style = os.getenv("VOICEVOX_STYLE_NAME", "ノーマル")
    r = requests.get(f"{BASE_URL}/speakers", timeout=30)
    r.raise_for_status()
    for speaker in r.json():
        if speaker.get("name") == name:
            return int(next((x["id"] for x in speaker["styles"] if x.get("name") == style), speaker["styles"][0]["id"]))
    raise RuntimeError(f"VOICEVOX speaker not found: {name}/{style}")

def synthesize(text: str, output_path: Path, speed: float, speaker_id=None):
    speaker_id = speaker_id if speaker_id is not None else resolve_speaker_id()
    q = requests.post(f"{BASE_URL}/audio_query", params={"text": text, "speaker": speaker_id}, timeout=60)
    q.raise_for_status()
    query = q.json()
    query["speedScale"] = speed
    query["outputSamplingRate"] = 48000
    s = requests.post(f"{BASE_URL}/synthesis", params={"speaker": speaker_id}, json=query, timeout=180)
    s.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(s.content)
    return output_path
