#!/bin/bash
# Скрипт полной остановки всей системы

echo "🛑 Остановка всей системы..."

cd /Users/bogdanprihodko/Bst

# Локальный клиент
echo "   Остановка локального клиента..."
pkill -f "client_live.py" && echo "   ✅ Локальный клиент остановлен" || echo "   ⚠️  Локальный клиент не найден"

# Локальный сервер (если был запущен)
echo "   Остановка локального сервера..."
pkill -f "server_simple.py" && echo "   ✅ Локальный сервер остановлен" || echo "   ⚠️  Локальный сервер не найден"

# Docker клиенты
echo "   Остановка Docker клиентов..."
docker-compose down 2>&1 | grep -E "Stopping|Removing" && echo "   ✅ Docker клиенты остановлены" || echo "   ⚠️  Docker клиенты не найдены"

# Удаленный сервер
echo "   Остановка удаленного сервера..."
if [ -n "$REMOTE_PASS" ]; then
    sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no ${REMOTE_USER:-root}@${REMOTE_HOST:-195.133.17.131} 'pkill -f server_simple.py' 2>&1 && echo "   ✅ Удаленный сервер остановлен" || echo "   ⚠️  Удаленный сервер не найден"
else
    echo "   ⚠️  REMOTE_PASS не установлен, пропускаю удаленный сервер"
fi

sleep 1

echo ""
echo "✅ Все процессы остановлены!"
echo ""

