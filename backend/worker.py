import time
import redis
import cv2
import os
from ultralytics import YOLO
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType

# ==================== КОНФИГУРАЦИЯ ====================
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'best.pt')
RESULT_DIR = os.path.join(PROJECT_ROOT, 'results')

print('╔════════════════════════════════════════════════╗')
print('║         SafetyGuard Worker v1.0.0              ║')
print('╚════════════════════════════════════════════════╝')
print()
print(f'PROJECT_ROOT: {PROJECT_ROOT}')
print(f'RESULT_DIR: {RESULT_DIR}')
print(f'MODEL_PATH: {MODEL_PATH}')
print()

# Создаем директорию для результатов
os.makedirs(RESULT_DIR, exist_ok=True)

# ==================== REDIS СОЕДИНЕНИЕ ====================
def connect_to_redis(max_retries=5, retry_delay=2):
    """Пытается подключиться к Redis с несколькими попытками"""
    for attempt in range(max_retries):
        try:
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
            r.ping()
            print('✓ Connected to Redis')
            return r
        except Exception as e:
            if attempt < max_retries - 1:
                print(f'⚠ Redis connection attempt {attempt + 1}/{max_retries} failed: {e}')
                print(f'  Retrying in {retry_delay} seconds...')
                time.sleep(retry_delay)
            else:
                print(f'✗ Failed to connect to Redis after {max_retries} attempts')
                print('  Please install and start Redis:')
                print('  - macOS: brew install redis && brew services start redis')
                print('  - Linux: sudo apt-get install redis-server && sudo systemctl start redis')
    return None

r = connect_to_redis()
print()

# ==================== ЗАГРУЗКА МОДЕЛИ ====================
print('Loading YOLO model...')

# Пути к моделям
ONNX_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'best.onnx')
QUANTIZED_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'best_quantized.onnx')


def create_quantized_model():
    """Создаёт квантованную модель из PyTorch модели"""
    print('  → Loading PyTorch model...')
    model = YOLO(MODEL_PATH)
    original_size = os.path.getsize(MODEL_PATH) / (1024 * 1024)
    print(f'  → Original PyTorch model size: {original_size:.2f} MB')

    # Экспортируем в ONNX
    print('  → Exporting to ONNX format...')
    model.export(format='onnx', half=False, imgsz=640, simplify=True)
    print(f'  → ONNX model exported to {ONNX_MODEL_PATH}')

    # Квантуем ONNX модель
    print('  → Applying dynamic quantization...')
    quantize_dynamic(
        ONNX_MODEL_PATH,
        QUANTIZED_MODEL_PATH,
        weight_type=QuantType.QUInt8
    )

    onnx_size = os.path.getsize(ONNX_MODEL_PATH) / (1024 * 1024)
    quantized_size = os.path.getsize(QUANTIZED_MODEL_PATH) / (1024 * 1024)
    reduction = (1 - quantized_size / onnx_size) * 100
    print(f'  → ONNX size: {onnx_size:.2f} MB → Quantized: {quantized_size:.2f} MB ({reduction:.1f}% reduction)')

    return QUANTIZED_MODEL_PATH


# Проверяем, существует ли квантованная модель
if os.path.exists(QUANTIZED_MODEL_PATH):
    print(f'✓ Loading existing quantized model from {QUANTIZED_MODEL_PATH}...')
    MODEL_PATH_TO_USE = QUANTIZED_MODEL_PATH
else:
    print('Creating quantized model...')
    try:
        MODEL_PATH_TO_USE = create_quantized_model()
    except Exception as e:
        print(f'✗ Error creating quantized model: {e}')
        print('  → Falling back to original PyTorch model')
        MODEL_PATH_TO_USE = MODEL_PATH

# Загружаем модель
try:
    model = YOLO(MODEL_PATH_TO_USE)
    model_size_mb = os.path.getsize(MODEL_PATH_TO_USE) / (1024 * 1024)
    print(f'✓ Model loaded successfully. Size: {model_size_mb:.2f} MB')
    print('✓ Worker started and ready to process tasks')
    print()
except Exception as e:
    print(f'✗ Error loading model: {e}')
    model = None

# Цвета для классов детекции
COLORS = {
    0: (0, 0, 255),    # helmet - красный (BGR)
    1: (0, 255, 255),  # vest - желтый (BGR)
    2: (0, 255, 0),    # head - зеленый (BGR)
    3: (255, 0, 0)     # person - синий (BGR)
}

CLASS_NAMES = {
    0: 'helmet',
    1: 'vest',
    2: 'head',
    3: 'person'
}

def process_video_file(task_id, input_path):
    """
    Обрабатывает видеофайл с использованием модели YOLO

    Args:
        task_id: Уникальный идентификатор задачи
        input_path: Путь к исходному видеофайлу

    Returns:
        bool: True если обработка успешна, False в противном случае
    """
    print(f'  → Starting processing for task {task_id}...')

    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():
        print(f'  ✗ Error opening video file: {input_path}')
        r.hset(f'task:{task_id}', 'status', 'error')
        return False

    # Получаем параметры видео
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f'  → Video info: {width}x{height} @ {fps:.2f}fps, {total_frames} frames')

    output_filename = f'{task_id}_result.mp4'
    output_path = os.path.join(RESULT_DIR, output_filename)

    # Создаем видео writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    try:
        frame_count = 0
        detections_total = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Детекция объектов
            results = model(frame, verbose=False)

            frame_detections = 0
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Получаем координаты и информацию о детекции
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    cls_name = CLASS_NAMES.get(cls_id, f'class_{cls_id}')

                    # Получаем цвет
                    color = COLORS.get(cls_id, (255, 255, 255))

                    # Рисуем bounding box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                    # Рисуем label
                    label = f'{cls_name} {conf:.2f}'
                    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
                    cv2.rectangle(frame, (x1, y1 - 20), (x1 + w, y1), color, -1)
                    cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

                    frame_detections += 1
                    detections_total += 1

            out.write(frame)
            frame_count += 1

            # Обновляем прогресс каждые 30 кадров
            if frame_count % 30 == 0:
                progress = int((frame_count / total_frames) * 100) if total_frames > 0 else 0
                r.hset(f'task:{task_id}', 'progress', progress)
                print(f'  → Task {task_id}: {progress}% complete ({frame_count}/{total_frames} frames) | Detections: {detections_total}')

        # Освобождаем ресурсы
        cap.release()
        out.release()

        # Обновляем статус задачи
        r.hset(f'task:{task_id}', mapping={
            'status': 'completed',
            'progress': 100,
            'result_path': output_path
        })

        print(f'  ✓ Task {task_id} completed. Total detections: {detections_total}')
        return True

    except Exception as e:
        print(f'  ✗ Error processing task {task_id}: {e}')
        import traceback
        traceback.print_exc()

        r.hset(f'task:{task_id}', 'status', 'error')
        r.hset(f'task:{task_id}', 'progress', 0)

        if cap:
            cap.release()
        if out:
            out.release()

        return False

# ==================== ГЛАВНЫЙ ЦИКЛ ====================
print('🔄 Worker is running and waiting for tasks...')
print()

task_counter = 0

while True:
    try:
        if r is None:
            print('⚠ Redis not connected, retrying in 5 seconds...')
            time.sleep(5)
            continue

        # Получаем задачу из очереди
        result = r.blpop('tasks_queue', timeout=5)
        if result is None:
            continue

        _, task_id_bytes = result
        task_id = task_id_bytes.decode('utf-8')
        task_counter += 1

        print(f'╔════════════════════════════════════════════════╗')
        print(f'║ Task #{task_counter}: {task_id[:8]}...                    ║')
        print(f'╚════════════════════════════════════════════════╝')

        # Получаем данные задачи
        task_data = r.hgetall(f'task:{task_id}')
        if task_data:
            input_path = task_data[b'input_path'].decode('utf-8') if b'input_path' in task_data else None

            # Если путь относительный, пробуем найти файл в uploads
            if input_path and not os.path.exists(input_path):
                if not os.path.isabs(input_path):
                    task_filename = os.path.basename(input_path)
                    alternative_path = os.path.join(PROJECT_ROOT, 'uploads', task_filename)
                    if os.path.exists(alternative_path):
                        print(f'  → Using alternative path: {alternative_path}')
                        input_path = alternative_path
                        r.hset(f'task:{task_id}', 'input_path', input_path)

            if input_path and os.path.exists(input_path):
                # Обновляем статус на 'processing'
                r.hset(f'task:{task_id}', 'status', 'processing')
                r.hset(f'task:{task_id}', 'progress', 0)

                # Запускаем обработку
                process_video_file(task_id, input_path)
            else:
                print(f'  ✗ Input file not found for task {task_id}: {input_path}')
                r.hset(f'task:{task_id}', 'status', 'error')
        else:
            print(f'  ✗ Task data not found for {task_id}')

        print()

    except KeyboardInterrupt:
        print()
        print('🛑 Worker stopped by user')
        break
    except Exception as e:
        print(f'  ✗ Error in worker loop: {e}')
        import traceback
        traceback.print_exc()
        time.sleep(5)


