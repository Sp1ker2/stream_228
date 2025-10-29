#!/bin/bash

echo "╔════════════════════════════════════════════════════╗"
echo "║      Запуск клиента для Mac (через venv)           ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Переходим в папку проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение
if [ -d "venv" ]; then
    echo "✅ Активируем venv..."
    source venv/bin/activate
else
    echo "📦 Создаем venv..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Устанавливаем зависимости..."
    pip install opencv-python pillow numpy requests
fi

echo ""
echo "🚀 Запускаем клиент..."
echo "📝 ВАЖНО: Mac запросит разрешение на запись экрана!"
echo "   Дайте разрешение в настройках macOS"
echo ""

# Запускаем клиент
    python client.py
    
    # После завершения - выход из venv
    deactivate

