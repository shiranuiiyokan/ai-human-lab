"""Drive-owned result journals; Sheets are synchronized by Scheduled Task.
Files must be precreated by the human Google account: service accounts have no quota.
"""
import json
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from drive_client import build_drive_service, list_child_folders, find_child, upsert_json
from youtube_upload import build_youtube_service, verify_channel


def read_json(drive, folder, name):
    f=find_child(drive,folder,name)
    if not f: raise RuntimeError(f'Missing precreated journal: {name}')
    return json.loads(drive.files().get_media(fileId=f['id']).execute())


def prepare(drive, folder, job):
    if os.getenv('PROJECT_NAMESPACE')!='AIHUMAN' or not job['project_id'].startswith('AIHUMAN-'):
        raise RuntimeError('Wrong project')
    if not job.get('queue_id') or not job.get('experiment_id'):
        raise RuntimeError('Queue identity missing')
    prior=read_json(drive,folder,'youtube_result.json')
    if prior.get('video_id'):
        raise RuntimeError('Already uploaded: reconcile stored video_id; do not reupload')
    read_json(drive,folder,'error.json')
    if job.get('production_date') and job['production_date']>datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Tokyo")).date().isoformat():
        raise RuntimeError('Future production date')


def reconcile():
    if os.getenv('PROJECT_NAMESPACE')!='AIHUMAN':raise RuntimeError('Wrong project')
    d=build_drive_service();y=build_youtube_service();channel=verify_channel(y)
    now=datetime.now(timezone.utc)
    for folder in list_child_folders(d,os.environ['AIHUMAN_DONE_FOLDER_ID'],limit=1000):
        file=find_child(d,folder['id'],'youtube_result.json')
        if not file:continue
        result=json.loads(d.files().get_media(fileId=file['id']).execute())
        if not result.get('video_id'):continue
        if not result.get('project_id','').startswith('AIHUMAN-'):raise RuntimeError('Foreign project')
        items=y.videos().list(part='snippet,status,statistics,contentDetails',id=result['video_id']).execute().get('items',[])
        if not items:continue
        v=items[0]
        if v['snippet']['channelId']!=channel:raise RuntimeError('Foreign channel')
        status=v['status'];result['youtube_status']=status
        result['title']=v['snippet']['title'];result['duration']=v['contentDetails']['duration']
        result['last_checked_at']=now.isoformat()
        result['sheet_sync_required']=True
        if status.get('uploadStatus') in {'failed','rejected','deleted'}:
            result['state']='failed';result['error_message']=status
        elif status['privacyStatus']=='public':
            result['state']='published';result['published_at']=v['snippet']['publishedAt']
            release=datetime.fromisoformat(result['published_at'].replace('Z','+00:00'))
            age=(now-release).total_seconds()/3600
            for label,hours in [('24h',24),('7d',168)]:
                if age>=hours and label not in result.get('metric_snapshots',{}):
                    stats=v.get('statistics',{})
                    if 'viewCount' in stats:
                        result.setdefault('metric_snapshots',{})[label]={'fetched_at':now.isoformat(),'age_hours':round(age,3),'late':age>hours+2,'statistics':stats}
        elif status.get('publishAt'):
            result['state']='scheduled';result['publish_at']=status['publishAt']
        else:
            result['state']=status['privacyStatus']
        result['analytics_metrics']='unavailable: Analytics OAuth scope not configured; do not invent CTR or retention'
        upsert_json(d,folder['id'],'youtube_result.json',result)
        print('RESULT_JOURNAL',json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':reconcile()
