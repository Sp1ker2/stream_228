#!/bin/bash
# Скрипт развертывания сервера на удаленный хост

REMOTE_HOST="${REMOTE_HOST:-195.133.17.131}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_PASS="${REMOTE_PASS}"
REMOTE_DIR="${REMOTE_DIR:-/root/screen_monitor}"
REMOTE_PORT="${REMOTE_PORT:-6789}"

if [ -z "$REMOTE_PASS" ]; then
    echo "❌ Ошибка: установите переменную REMOTE_PASS"
    echo "   export REMOTE_PASS='ваш_пароль'"
    exit 1
fi

echo "🚀 Развертывание сервера на $REMOTE_HOST..."

# Установка sshpass если нет (для автоматического ввода пароля)
if ! command -v sshpass &> /dev/null; then
    echo "📦 Установка sshpass..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install sshpass 2>/dev/null || echo "⚠️  Установите sshpass вручную: brew install hudochenko/sshpass/sshpass"
    else
        sudo apt-get install -y sshpass 2>/dev/null || echo "⚠️  Установите sshpass вручную"
    fi
fi

# Создание директории на удаленном сервере
echo "📁 Создание директории на сервере..."
sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" \
    "mkdir -p $REMOTE_DIR && mkdir -p $REMOTE_DIR/temp_recordings"

# Копирование файлов
echo "📤 Копирование файлов..."
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no \
    server_simple.py \
    requirements.txt \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

# Установка зависимостей и запуск сервера
echo "🔧 Установка зависимостей и запуск сервера..."
sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" << EOF
cd $REMOTE_DIR

# Создание виртуального окружения если нет
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Активация и установка зависимостей
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Остановка старого процесса если запущен
pkill -f server_simple.py || true
sleep 2

# Запуск сервера в фоне
nohup python3 server_simple.py > server.log 2>&1 &

echo "✅ Сервер запущен!"
echo "📹 Откройте: http://$REMOTE_HOST:$REMOTE_PORT"
EOF

echo ""
echo "✅ Развертывание завершено!"
echo "📹 Сервер доступен: http://$REMOTE_HOST:$REMOTE_PORT"
echo "📋 Логи: ssh $REMOTE_USER@$REMOTE_HOST 'tail -f $REMOTE_DIR/server.log'"

