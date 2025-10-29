#!/bin/bash
# Запуск локального клиента для отправки реального экрана MacBook на удаленный сервер

cd /Users/bogdanprihodko/Bst

# Активация виртуального окружения
source venv/bin/activate

# Остановка старого процесса если запущен
pkill -f "client_live.py" || true
sleep 2

# Получаем имя машины
MACHINE_NAME=$(hostname)_$(whoami)
echo "🖥️  Запуск для машины: $MACHINE_NAME"
echo "📡 Сервер: 195.133.17.131:6789"

# Запуск клиента с реальным экраном (без симуляции)
export MACHINE_ID="$MACHINE_NAME"
export SERVER_HOST="195.133.17.131"
export SERVER_PORT="6789"
export SIMULATE_SCREEN="false"

echo "🚀 Запускаю client_live.py..."
python3 client_live.py

