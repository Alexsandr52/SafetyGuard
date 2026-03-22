# SafetyGuard

<div align="center">

![SafetyGuard](https://img.shields.io/badge/SafetyGuard-v1.0.0-purple)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![YOLO](https://img.shields.io/badge/YOLO-v8-orange)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)


**Система детекции безопасности на рабочей площадке**

[Функциональности](#функциональности) • [Установка](#установка) • [Использование](#использование) • [API](#api-эндпоинты)

</div>

---

## Описание

**SafetyGuard** — это современная система компьютерного зрения для автоматического мониторинга соблюдения правил безопасности на промышленных и строительных объектах. Система использует передовую модель YOLOv8 с квантованием INT8 для быстрой и точной детекции объектов безопасности.

### Ключевые особенности

- 🚀 **Высокая производительность**: Квантование модели до INT8 для ускорения работы
- ⚡ **Асинхронная обработка**: Redis Queue для эффективной обработки видео
- 🎯 **Точная детекция**: 4 класса объектов: каски, жилеты, головы, люди
- 🌐 **Современный интерфейс**: Адаптивный веб-интерфейс на Tailwind CSS
- 📊 **Отслеживание прогресса**: Реальное время обновление статуса обработки
- 🎨 **Визуализация**: Красивая разметка bounding boxes с процентами уверенности

---

## Функциональности

### Детекция объектов

| Класс | Цвет | Описание | Статус |
|-------|------|----------|--------|
| 🪖 **Каска** | 🔴 Красный | Строительная каска | ✅ Безопасность |
| 👕 **Жилет** | 🟡 Желтый | Защитный жилет | ✅ Безопасность |
| 👤 **Голова** | 🟢 Зеленый | Голова без каски | ⚠️ Предупреждение |
| 🧍 **Человек** | 🔵 Синий | Любой человек | ℹ️ Информация |

### Технические характеристики

```
📦 Модель:          YOLOv8
🔢 Квантование:     INT8 (беззнаковое)
⚡ Брокер очередей: Redis
🌐 API:            FastAPI
🎨 Frontend:        Tailwind CSS + FontAwesome
📹 Форматы видео:   MP4, AVI, MOV
🖼️ Размер ввода:    640x640
```

---

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/SafetyGuard.git
cd SafetyGuard
```

### 2. Создание виртуального окружения

```bash
# Linux/macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r req.txt
```

### 4. Установка Redis

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows
# Скачайте и установите Redis for Windows
# https://github.com/microsoftarchive/redis/releases
```

### 5. Проверка Redis

```bash
redis-cli ping
# Должно вернуть: PONG
```

---

## Использование

### Запуск проекта

Откройте два терминала:

#### Терминал 1: Запуск API сервера

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Терминал 2: Запуск Worker

```bash
cd backend
python worker.py
```

### Доступ к интерфейсу

Откройте браузер и перейдите по адресу:

```
http://localhost:8000
```

### Использование веб-интерфейса

1. **Загрузка видео**: Перетащите видеофайл в зону загрузки или нажмите для выбора
2. **Отслеживание прогресса**: Наблюдайте за обработкой в реальном времени
3. **Скачивание результата**: После завершения загрузите видео с разметкой

---

## API Эндпоинты

### 1. Загрузка видео

```http
POST /process-video/
Content-Type: multipart/form-data
```

**Параметры:**
- `file` (required): Видеофайл

**Ответ:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

---

### 2. Проверка статуса

```http
GET /status/{task_id}
```

**Ответ:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45
}
```

**Статусы:**
- `queued` — задача в очереди
- `processing` — видео обрабатывается
- `completed` — обработка завершена
- `error` — произошла ошибка

---

### 3. Скачивание результата

```http
GET /download/{task_id}
```

**Ответ:**
- Возвращает обработанный видеофайл

---

## Структура проекта

```
SafetyGuard/
├── backend/
│   ├── main.py              # FastAPI сервер
│   ├── worker.py            # Worker для обработки видео
│   ├── best.pt              # YOLO модель (PyTorch)
│   ├── best.onnx            # YOLO модель (ONNX)
│   ├── best_quantized.onnx  # Квантованная модель
│   ├── requirements.txt     # Зависимости
│   ├── uploads/             # Загруженные видео
│   └── results/             # Обработанные видео
├── frontend/
│   └── index.html           # Веб-интерфейс
├── venv/                    # Виртуальное окружение
├── uploads/                 # Загруженные файлы
├── results/                 # Результаты обработки
├── README.md                # Документация
└── req.txt                  # Зависимости проекта
```

---

## Квантование модели

Процесс квантования автоматически выполняется при первом запуске:

1. **PyTorch** → **ONNX**: Экспорт модели
2. **ONNX FP32** → **ONNX INT8**: Динамическое квантование

```python
# Пример квантования (автоматически в worker.py)
from onnxruntime.quantization import quantize_dynamic, QuantType

quantize_dynamic(
    'best.onnx',
    'best_quantized.onnx',
    weight_type=QuantType.QUInt8
)
```

**Результаты квантования:**
- Размер модели: ↓ 50-70%
- Скорость инференса: ↑ 2-3x (CPU)
- Точность: ~95% от исходной

---

## Troubleshooting

### Redis не запускается

```bash
# Проверьте статус
redis-cli ping

# Если не работает, перезапустите
# macOS
brew services restart redis

# Linux
sudo systemctl restart redis
```

### Модель не загружается

Убедитесь, что файлы моделей существуют:
```bash
ls -lh backend/best.pt
ls -lh backend/best.onnx
ls -lh backend/best_quantized.onnx
```

### Ошибки CORS

Для продакшена измените настройки CORS в `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://yourdomain.com'],  # Ваш домен
    ...
)
```

### Проблемы с памятью

Для больших видео увеличьте размер кэша Redis:
```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

---

## Производительность

### Бенчмарки

| Параметр | Без квантования | С квантованием |
|----------|----------------|----------------|
| Размер модели | 12.4 MB | 3.3 MB |
| Время обработки (1 мин видео) | ~120s | ~45s |
| FPS | 8-10 | 20-25 |
| mAP@50 | 0.89 | 0.87 |

### Оптимизация для продакшена

1. **Используйте GPU**: `model = YOLO('best.pt').to('cuda')`
2. **Батчовая обработка**: Обработка нескольких кадров одновременно
3. **Downsampling**: Снижение разрешения для preview
4. **Кэширование**: Кэширование часто используемых видео

---

## Roadmap

- [ ] Поддержка GPU (CUDA)
- [ ] Детекция дополнительных объектов (обувь, очки)
- [ ] Отслеживание объектов (tracking)
- [ ] Аналитика нарушений
- [ ] Уведомления (email, Telegram)
- [ ] Docker контейнеризация
- [ ] RESTful API документация (Swagger)

