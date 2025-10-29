#!/bin/bash
# Пример конфигурационного файла
# Скопируйте в config.sh и заполните своими данными
# git не отслеживает config.sh (он в .gitignore)

export REMOTE_HOST="195.133.17.131"
export REMOTE_USER="root"
export REMOTE_PASS="your_password_here"
export REMOTE_DIR="/root/screen_monitor"
export REMOTE_PORT="6789"

# Данные для веб-панели (необязательно)
export PANEL_URL="https://195.133.17.131:16205/df2d94ee"
export PANEL_USER="your_username"
export PANEL_PASS="your_password"

