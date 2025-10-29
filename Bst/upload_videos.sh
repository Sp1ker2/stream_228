#!/bin/bash

echo "📤 Загрузка видео на сервер..."

cd ~/Bst/temp_recordings

for video in *.mp4; do
    if [ -f "$video" ]; then
        echo "Загружаю: $video"
        curl -X POST \
            -F "video=@$video" \
            -F "machine_id=MacBook-Air-3.local_root" \
            -F "timestamp=$(date +%Y%m%d_%H%M%S)" \
            http://195.133.17.131:5000/upload
        echo ""
        rm "$video"
    fi
done

echo "✅ Готово! Откройте: http://195.133.17.131:5000"





