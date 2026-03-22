#!/bin/bash

# SafetyGuard Start Script
# Запуск проекта SafetyGuard

echo "╔════════════════════════════════════════════════╗"
echo "║         SafetyGuard - Start Script              ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Проверка Redis
echo "Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis is running"
else
    echo "✗ Redis is not running. Please start Redis first:"
    echo "  brew services start redis  # macOS"
    echo "  sudo systemctl start redis # Linux"
    exit 1
fi

# Создание директорий
echo ""
echo "📁 Creating directories..."
mkdir -p uploads results backend

# Запуск API сервера (фоновый режим)
echo ""
echo "🚀 Starting API server..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
echo "✓ API server started (PID: $API_PID)"

# Запуск Worker (фоновый режим)
echo ""
echo "Starting Worker..."
python backend/worker.py &
WORKER_PID=$!
echo "✓ Worker started (PID: $WORKER_PID)"

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║         SafetyGuard is running!                  ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "📊 API Dashboard: http://localhost:8000/docs"
echo "🌐 Web Interface: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Обработка Ctrl+C
trap "echo ''; echo 'Stopping services...'; kill $API_PID $WORKER_PID; exit 0" INT TERM

# Ожидание завершения процессов
wait
