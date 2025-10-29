#!/bin/bash
# Скрипт полного запуска всей системы

echo "🚀 Запуск всей системы..."

cd /Users/bogdanprihodko/Bst

# Удаленный сервер
echo "   1️⃣  Запуск удаленного сервера..."
./deploy_server.sh 2>&1 | tail -3
sleep 3

# Docker клиенты
echo ""
echo "   2️⃣  Запуск Docker клиентов..."
docker-compose up -d 2>&1 | tail -3
sleep 2

# Локальная машина
echo ""
echo "   3️⃣  Запуск вашей машины..."
./START_MY_MACHINE.sh > /dev/null 2>&1 &
sleep 2

echo ""
echo "✅ Все запущено!"
echo ""
echo "📹 Откройте в браузере:"
echo "   http://195.133.17.131:6789"
echo ""
echo "🔍 Проверка статуса:"
ps aux | grep "client_live.py" | grep -v grep > /dev/null && echo "   ✅ Ваша машина работает" || echo "   ❌ Ваша машина не запущена"
docker ps | grep screen_monitor > /dev/null && echo "   ✅ Docker клиенты работают" || echo "   ❌ Docker клиенты не запущены"
curl -s http://195.133.17.131:6789 > /dev/null && echo "   ✅ Удаленный сервер работает" || echo "   ❌ Удаленный сервер недоступен"

