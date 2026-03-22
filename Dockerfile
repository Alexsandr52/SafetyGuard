FROM python:3.11-slim

# Установка системных зависимостей для OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование зависимостей
COPY req.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r req.txt

# Копирование файлов проекта
COPY . .

# Создание необходимых директорий
RUN mkdir -p uploads results backend frontend

# Установка прав доступа
RUN chmod -R 755 /app

# Экспорт портов
EXPOSE 8000

# Команда по умолчанию
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
