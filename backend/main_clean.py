import os
import uuid
import redis
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="SafetyGuard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')
UPLOAD_DIR = os.path.join(PROJECT_ROOT, 'uploads')
RESULT_DIR = os.path.join(PROJECT_ROOT, 'results')

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(FRONTEND_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Глобальная переменная для Redis
r = None

def ensure_redis():
    """Убедится, что Redis подключен"""
    global r
    if r is None:
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
            r.ping()
            print('✓ Redis connected')
        except Exception as e:
            print(f'✗ Redis error: {e}')
            return False
    return True

@app.get('/')
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")

@app.post('/process-video/')
async def process_video(file: UploadFile = File(...)):
    if not ensure_redis():
        raise HTTPException(status_code=503, detail='Redis not available')

    try:
        task_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1] or '.mp4'
        input_path = os.path.join(UPLOAD_DIR, task_id + file_extension)

        with open(input_path, 'wb') as buffer:
            buffer.write(await file.read())

        task_data = {
            'task_id': task_id,
            'input_path': input_path,
            'status': 'queued',
            'progress': '0'
        }

        r.hset('task:' + task_id, mapping=task_data)
        r.rpush('tasks_queue', task_id)
        print(f'✓ Task {task_id} queued')

        return {'task_id': task_id, 'status': 'queued'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/status/{task_id}')
async def get_status(task_id: str):
    if not ensure_redis():
        raise HTTPException(status_code=503, detail='Redis not available')

    try:
        task_data = r.hgetall('task:' + task_id)
        if not task_data:
            raise HTTPException(status_code=404, detail='Task not found')

        return {
            'task_id': task_id,
            'status': task_data.get(b'status', b'unknown').decode('utf-8'),
            'progress': int(task_data.get(b'progress', b'0').decode('utf-8'))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/download/{task_id}')
async def download_video(task_id: str):
    if not ensure_redis():
        raise HTTPException(status_code=503, detail='Redis not available')

    try:
        task_data = r.hgetall('task:' + task_id)
        if not task_data or task_data.get(b'status').decode('utf-8') != 'completed':
            raise HTTPException(status_code=404, detail='Video not ready')

        result_path = os.path.join(RESULT_DIR, task_id + '_result.mp4')
        if os.path.exists(result_path):
            print(f'✓ Downloading {task_id}')
            return FileResponse(result_path, media_type='video/mp4', filename=task_id + '_result.mp4')

        raise HTTPException(status_code=404, detail='Result file missing')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
