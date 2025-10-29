#!/bin/bash
# Скрипт для запуска Docker клиентов

echo "🐳 Запуск Docker клиентов..."
echo "============================================================"

# Строим образ
echo "📦 Сборка Docker образа..."
docker-compose build

# Запускаем всех клиентов
echo "🚀 Запуск клиентов..."
docker-compose up -d

# Показываем статус
echo ""
echo "✅ Клиенты запущены:"
docker-compose ps

echo ""
echo "📊 Логи можно посмотреть командой:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Остановка всех клиентов:"
echo "   docker-compose down"
echo ""
echo "🌐 Откройте в браузере:"
echo "   http://localhost:6789"

