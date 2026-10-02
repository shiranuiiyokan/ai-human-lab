import json
import os
import shutil
from pathlib import Path

from drive_client import build_drive_service, download_job_folder, list_child_folders, move_folder, upsert_json
from render_video import render
from youtube_upload import upload_video
from voicevox import wait_until_ready

WORK_ROOT = Path("work")
PROJECT_NAMESPACE = os.getenv("PROJECT_NAMESPACE", "")

def validate_job(job):
    if PROJECT_NAMESPACE != "AIHUMAN":
        raise RuntimeError("ABORT: PROJECT_NAMESPACE must be AIHUMAN")
    pid = str(job.get("project_id",""))
    if not pid.startswith("AIHUMAN-"):
        raise ValueError("project_id must start with AIHUMAN-")
    age = int(job.get("subject_age_min", job.get("experiment",{}).get("subject_age_min", 0)) or 0)
    if age < 20:
        raise ValueError("subject_age_min must be >= 20")
    y = job.get("youtube",{})
    if y.get("made_for_kids") is not False:
        raise ValueError("made_for_kids must be false")
    if y.get("contains_synthetic_media") is not True:
        raise ValueError("contains_synthetic_media must be true")
    if not job.get("scenes"):
        raise ValueError("scenes missing")

def process_one(service, category, parent_id, folder, done_id, error_id):
    job_dir = WORK_ROOT / category / folder["id"]
    shutil.rmtree(job_dir, ignore_errors=True)
    try:
        download_job_folder(service, folder["id"], job_dir)
        manifest = job_dir / "manifest.json"
        if not manifest.exists():
            raise FileNotFoundError("manifest.json")
        job = json.loads(manifest.read_text(encoding="utf-8"))
        validate_job(job)
        wait_until_ready()
        output = job_dir / "rendered.mp4"
        render(job, job_dir, output)
        result = upload_video(output, job)
        result.update({"project_id":job["project_id"],"category":category})
        upsert_json(service, folder["id"], "youtube_result.json", result)
        move_folder(service, folder["id"], parent_id, done_id)
        print("SUCCESS", json.dumps(result, ensure_ascii=False), flush=True)
        return True
    except Exception as exc:
        err={"folder":folder.get("name"),"type":type(exc).__name__,"message":str(exc)}
        try:
            upsert_json(service, folder["id"], "error.json", err)
            move_folder(service, folder["id"], parent_id, error_id)
        except Exception as move_exc:
            print("ERROR while recording failure:", move_exc, flush=True)
        print("FAIL", json.dumps(err, ensure_ascii=False), flush=True)
        return False

def main():
    if PROJECT_NAMESPACE != "AIHUMAN":
        raise SystemExit("ABORT: wrong namespace")
    service=build_drive_service()
    cfg=[
        ("short",os.environ["AIHUMAN_SHORT_FOLDER_ID"],int(os.getenv("SHORT_JOB_LIMIT","3"))),
        ("long",os.environ["AIHUMAN_LONG_FOLDER_ID"],int(os.getenv("LONG_JOB_LIMIT","1"))),
    ]
    done_id=os.environ["AIHUMAN_DONE_FOLDER_ID"]
    error_id=os.environ["AIHUMAN_ERROR_FOLDER_ID"]
    processed=0
    failures=0
    for category,parent_id,limit in cfg:
        folders=list_child_folders(service,parent_id,limit=limit)
        for folder in folders:
            processed+=1
            if not process_one(service,category,parent_id,folder,done_id,error_id):
                failures+=1
    print(json.dumps({"processed":processed,"failures":failures},ensure_ascii=False))
    if failures and processed == failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
