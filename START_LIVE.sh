#!/bin/bash

echo "╔════════════════════════════════════════════════════╗"
echo "║  Запуск клиента с LIVE трансляцией                 ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

if [ -d "venv" ]; then
    echo "✅ Активируем venv..."
    source venv/bin/activate
else
    echo "📦 Создаем venv..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Устанавливаем зависимости..."
    pip install opencv-python pillow numpy requests flask -q
fi

echo ""
echo "🚀 Запускаем клиент с LIVE трансляцией..."
echo "   - Запись каждые 5 минут"
echo "   - Прямая трансляция активна"
echo ""
echo "🌐 Откройте для просмотра:"
echo "   http://localhost:6789"
echo "   http://localhost:6789/live"
echo ""

python3 client_live.py





