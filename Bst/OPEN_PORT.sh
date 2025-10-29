#!/bin/bash
# Скрипт открытия порта 6789 на удаленном сервере через SSH

REMOTE_HOST="195.133.17.131"
REMOTE_USER="root"
REMOTE_PASS="iFG02M6Z"

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
echo "   Логин: th3dw0l9"
echo "   Пароль: a8188437"
EOF

echo "✅ Готово!"

