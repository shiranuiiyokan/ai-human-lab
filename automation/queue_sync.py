"""Human-only queue/result reconciliation; never uploads videos."""
import json
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from googleapiclient.discovery import build
from drive_client import drive_credentials
from youtube_upload import build_youtube_service, verify_channel

SHEET_ID = '1Lliq2vUmS5e_GSGLaha4xj-lfk4WZIVzpt523qA-ukY'

def sheets_service():
    if os.getenv('PROJECT_NAMESPACE') != 'AIHUMAN':
        raise RuntimeError('Wrong namespace')
    return build('sheets', 'v4', credentials=drive_credentials().with_scopes(['https://www.googleapis.com/auth/spreadsheets']), cache_discovery=False)

def rows(s, tab):
    return s.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=f'{tab}!A3:T500').execute().get('values', [])

def write(s, range_name, values):
    return s.spreadsheets().values().update(spreadsheetId=SHEET_ID, range=range_name, valueInputOption='RAW', body={'values':values}).execute()

def cell(row, n):
    return row[n] if n < len(row) else ''

def queue_row(s, queue_id):
    data = rows(s, 'Production_Queue')
    matches = [(n+3, r) for n,r in enumerate(data) if cell(r,0)==queue_id]
    if len(matches)!=1:
        raise RuntimeError(f'Queue ID must be unique: {queue_id}')
    return matches[0]

def preflight(job):
    s=sheets_service()
    n,r=queue_row(s, job['queue_id'])
    if cell(r,3)!=job['experiment_id']:
        raise RuntimeError('Queue experiment mismatch')
    if cell(r,9) not in {'queued','producing','produced','uploading'}:
        raise RuntimeError(f'Queue not uploadable: {cell(r,9)}')
    if cell(r,18):
        raise RuntimeError('Queue already has video_id; reconcile instead of uploading')
    write(s,f'Production_Queue!J{n}',[['uploading']])
    return s

def log_result(s, job, result):
    n,r=queue_row(s,job['queue_id'])
    state='scheduled' if result.get('publish_at') else 'uploaded'
    write(s,f'Production_Queue!J{n}',[[state]])
    write(s,f'Production_Queue!S{n}:T{n}',[[result['video_id'],'']])
    existing=rows(s,'Result_Log')
    if any(cell(r,0)==result['video_id'] for r in existing):
        return
    meta={'queue_id':job['queue_id'],'project_id':job['project_id'],'publish_at':result.get('publish_at'),'state':state,'attraction_tag':job.get('attraction_tag'),'metrics_status':'pending; Analytics-only metrics unavailable without Analytics OAuth scope'}
    row=[result['video_id'],job['experiment_id'],(result.get('publish_at') or datetime.now(timezone.utc).isoformat())[:10], 'Short']+['']*12+[json.dumps(meta,ensure_ascii=False)]
    target=3+len(existing)
    write(s,f'Result_Log!A{target}:Q{target}',[row])

def log_error(job, exc):
    s=sheets_service()
    n,r=queue_row(s,job['queue_id'])
    write(s,f'Production_Queue!J{n}',[['failed']])
    write(s,f'Production_Queue!T{n}',[[json.dumps({'reason':type(exc).__name__,'error_message':str(exc)},ensure_ascii=False)]])

def reconcile():
    s=sheets_service()
    y=build_youtube_service()
    channel=verify_channel(y)
    data=rows(s,'Result_Log')
    queue=rows(s,'Production_Queue')
    now=datetime.now(timezone.utc)
    for i,row in enumerate(data[1:],4):
        vid=cell(row,0)
        if not vid: continue
        found=y.videos().list(part='snippet,status,statistics',id=vid).execute().get('items',[])
        if not found: continue
        v=found[0]
        if v['snippet']['channelId']!=channel: raise RuntimeError('Foreign channel in Result_Log')
        try: meta=json.loads(cell(row,16))
        except (ValueError,TypeError): meta={'original_note':cell(row,16)}
        status=v['status']['privacyStatus']
        if status!='public':
            meta['state']='scheduled' if v['status'].get('publishAt') else status
            write(s,f'Result_Log!Q{i}',[[json.dumps(meta,ensure_ascii=False)]])
            continue
        # YouTube publishedAt on a public video is the public release time.
        released=datetime.fromisoformat(v['snippet']['publishedAt'].replace('Z','+00:00'))
        meta['state']='published';meta['published_at']=released.isoformat()
        for qn,qr in enumerate(queue[1:],4):
            if cell(qr,18)==vid:
                write(s,f'Production_Queue!J{qn}',[['published']])
        write(s,f'Result_Log!C{i}',[[released.astimezone(ZoneInfo('Asia/Tokyo')).date().isoformat()]])
        age=now-released
        stats=v.get('statistics',{})
        for label,hours,col in [('24h',24,'E'),('7d',168,'F')]:
            # Capture within the first hourly window; explicitly label late samples.
            if age>=timedelta(hours=hours) and not meta.get(f'sampled_{label}_at') and cell(row,4 if col=='E' else 5)=='':
                meta[f'sampled_{label}_at']=now.isoformat()
                meta[f'sample_{label}_age_hours']=round(age.total_seconds()/3600,2)
                meta[f'sample_{label}_late']=age>timedelta(hours=hours+2)
                meta[f'stats_{label}']=stats
                write(s,f'Result_Log!{col}{i}',[[int(stats.get('viewCount',0))]])
                write(s,f'Result_Log!K{i}:L{i}',[[int(stats.get('likeCount',0)),int(stats.get('commentCount',0))]])
        write(s,f'Result_Log!Q{i}',[[json.dumps(meta,ensure_ascii=False)]])
    print('Human Result_Log reconciliation complete')

if __name__=='__main__':
    reconcile()
