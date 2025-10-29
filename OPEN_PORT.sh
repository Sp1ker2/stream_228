#!/bin/bash
# Скрипт открытия порта 6789 на удаленном сервере через SSH

REMOTE_HOST="${REMOTE_HOST:-195.133.17.131}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_PASS="${REMOTE_PASS}"

if [ -z "$REMOTE_PASS" ]; then
    echo "❌ Ошибка: установите переменную REMOTE_PASS"
    echo "   export REMOTE_PASS='ваш_пароль'"
    exit 1
fi

echo "🔓 Открытие порта 6789 на сервере..."

sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
# Проверка UFW
if command -v ufw &> /dev/null; then
    echo "📋 Настройка UFW..."
    ufw allow 6789/tcp
    ufw status | grep 6789 || echo "⚠️  Проверьте UFW вручную"
fi

# Проверка firewall-cmd
if command -v firewall-cmd &> /dev/null; then
    echo "📋 Настройка firewalld..."
    firewall-cmd --permanent --add-port=6789/tcp
    firewall-cmd --reload
fi

# Проверка iptables (если используется)
echo "📋 Проверка порта 6789..."
netstat -tuln | grep 6789 || echo "⚠️  Порт не слушается (возможно сервер не запущен)"
echo ""
echo "💡 Если порт не открыт, откройте его через панель управления:"
echo "   https://195.133.17.131:16205/df2d94ee"
echo "   Логин: [установить PANEL_USER в config.sh]"
echo "   Пароль: [установить PANEL_PASS в config.sh]"
EOF

echo "✅ Готово!"

