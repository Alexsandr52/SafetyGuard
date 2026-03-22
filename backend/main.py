import os
import uuid
import redis
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="SafetyGuard API",
    description="Система детекции безопасности с использованием YOLOv8",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Получаем путь к корневой директории проекта
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')
UPLOAD_DIR = os.path.join(PROJECT_ROOT, 'uploads')
RESULT_DIR = os.path.join(PROJECT_ROOT, 'results')

# Создаем директории если их нет
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

print(f'PROJECT_ROOT: {PROJECT_ROOT}')
print(f'FRONTEND_DIR: {FRONTEND_DIR}')
print(f'UPLOAD_DIR: {UPLOAD_DIR}')
print(f'RESULT_DIR: {RESULT_DIR}')

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=False)
    r.ping()
    print(f'✓ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}')
except Exception as e:
    print(f'✗ Error connecting to Redis: {e}')
    print('  Please install and start Redis:')
    print('  - macOS: brew install redis && brew services start redis')
    print('  - Linux: sudo apt-get install redis-server && sudo systemctl start redis')
    print('  - Docker: Ensure redis service is running in docker-compose')
    r = None


@app.get('/')
async def root():
    """Redirect to frontend"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")


@app.post('/process-video/')
async def process_video(file: UploadFile = File(...)):
    """
    Принимает видеофайл для обработки и ставит в очередь

    - **file**: Видеофайл для обработки (MP4, AVI, MOV)

    Returns:
        - task_id: Уникальный идентификатор задачи
        - status: Статус задачи (queued)
    """
    if r is None:
        raise HTTPException(status_code=503, detail='Redis connection not available')

    try:
        task_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1] or '.mp4'
        input_path = os.path.join(UPLOAD_DIR, f'{task_id}{file_extension}')

        # Сохраняем файл
        with open(input_path, 'wb') as buffer:
            buffer.write(await file.read())

        task_data = {
            'task_id': task_id,
            'input_path': input_path,
            'status': 'queued',
            'progress': '0'
        }

        # Запись в Redis
        r.hset(f'task:{task_id}', mapping=task_data)
        r.rpush('tasks_queue', task_id)

        print(f'✓ Task {task_id} queued for processing')

        return {'task_id': task_id, 'status': 'queued'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error processing video: {str(e)}')


@app.get('/status/{task_id}')
async def get_status(task_id: str):
    """
    Проверяет статус обработки видео

    - **task_id**: Идентификатор задачи

    Returns:
        - task_id: Идентификатор задачи
        - status: Статус (queued, processing, completed, error)
        - progress: Прогресс в процентах (0-100)
    """
    try:
        task_data = r.hgetall(f'task:{task_id}')
        if not task_data:
            raise HTTPException(status_code=404, detail='Task not found')

        return {
            'task_id': task_id,
            'status': task_data.get(b'status', b'unknown').decode('utf-8'),
            'progress': int(task_data.get(b'progress', b'0').decode('utf-8'))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error getting status: {str(e)}')


@app.get('/download/{task_id}')
async def download_video(task_id: str):
    """
    Скачивает обработанное видео

    - **task_id**: Идентификатор задачи

    Returns:
        - File: Обработанное видеофайл
    """
    try:
        task_data = r.hgetall(f'task:{task_id}')
        if not task_data or task_data.get(b'status').decode('utf-8') != 'completed':
            raise HTTPException(status_code=404, detail='Video not ready or task not found')

        result_filename = f'{task_id}_result.mp4'
        result_path = os.path.join(RESULT_DIR, result_filename)

        if os.path.exists(result_path):
            print(f'✓ Downloading result for task {task_id}')
            return FileResponse(result_path, media_type='video/mp4', filename=f'processed_{task_id}.mp4')

        raise HTTPException(status_code=404, detail='Result file missing')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error downloading video: {str(e)}')