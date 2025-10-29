#!/usr/bin/env python3
"""Сервер с прямой трансляцией"""
from flask import Flask, send_file, Response, jsonify, request
from pathlib import Path
import time
import base64
import threading

app = Flask(__name__)
VIDEOS = Path("temp_recordings")
VIDEOS.mkdir(exist_ok=True)

# Глобальная переменная для хранения последнего кадра
last_frame = None
frame_lock = threading.Lock()

@app.route('/')
def index():
    videos = list(VIDEOS.glob('*.mp4'))
    
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8">
    <title>📹 Screen Monitor</title>
    <style>
        body{{font-family:Arial;background:#f5f5f5;padding:30px;max-width:1400px;margin:0 auto}}
        h1{{color:#333}} 
        .video{{background:white;padding:20px;margin:15px 0;border-radius:10px}}
        .info{{color:#666;margin:10px 0}} 
        .btn{{background:#4CAF50;color:white;padding:12px 25px;
        text-decoration:none;border-radius:5px;display:inline-block;margin:5px}}
        .live-btn{{background:#ff0000;color:white;padding:15px 30px;
        text-decoration:none;border-radius:8px;font-size:1.2em;font-weight:bold;
        animation: pulse 2s infinite;}}
        @keyframes pulse {{0%,100%{{opacity:1}} 50%{{opacity:0.7}}}}
        #liveView{{background:#000;border-radius:10px;padding:20px;margin:20px 0}}
        #liveFrame{{max-width:100%;border-radius:5px}}
    </style>
    </head>
    <body>
        <h1>📹 Screen Monitor</h1>
        
        <div style="text-align:center;margin:30px 0">
            <a href="/live" class="live-btn">🔴 СМОТРЕТЬ ПРЯМУЮ ТРАНСЛЯЦИЮ</a>
        </div>
        
        <h2>📁 Сохраненные записи ({len(videos)} видео):</h2>
    """
    
    for v in sorted(videos, reverse=True):
        mb = v.stat().st_size / (1024*1024)
        html += f"""
        <div class="video">
            <h3>{v.name}</h3>
            <div class="info">Размер: {mb:.2f} MB</div>
            <video width="100%" controls>
                <source src="/video/{v.name}" type="video/mp4">
            </video>
        </div>
        """
    
    html += "</body></html>"
    return html

@app.route('/live')
def live_view():
    """Прямая трансляция"""
    html = """
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8">
    <title>🔴 LIVE Stream</title>
    <style>
        body{font-family:Arial;background:#000;padding:20px;margin:0}
        h1{color:white;text-align:center}
        #frame{display:block;margin:0 auto;max-width:100%;border-radius:10px}
        .status{color:#0f0;text-align:center;font-size:1.2em}
    </style></head>
    <body>
        <h1>🔴 ПРЯМАЯ ТРАНСЛЯЦИЯ</h1>
        <div class="status" id="status">● Подключение...</div>
        <img id="frame" src="/stream" style="display:none">
        
        <script>
            const img = document.getElementById('frame');
            let lastUpdate = Date.now();
            
            function reload() {
                lastUpdate = Date.now();
                img.src = '/stream?t=' + Date.now();
            }
            
            img.onload = function() {
                img.style.display = 'block';
                document.getElementById('status').textContent = '● Live';
                setTimeout(reload, 100); // Обновляем каждые 100мс
            };
            
            img.onerror = function() {
                setTimeout(reload, 1000);
            };
            
            // Проверка активности
            setInterval(() => {
                if (Date.now() - lastUpdate > 5000) {
                    document.getElementById('status').textContent = '● Соединение потеряно';
                }
            }, 1000);
            
            reload();
        </script>
    </body></html>
    """
    return html

@app.route('/stream')
def stream():
    """Отдача последнего кадра"""
    with frame_lock:
        if last_frame:
            return Response(last_frame, mimetype='image/jpeg')
    
    # Возвращаем черный кадр если нет данных
    black_frame = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' "\\x1c\\x0c\\x1a\'<(.7\'<=\x18@'
    return Response(black_frame, mimetype='image/jpeg')

@app.route('/api/upload_frame', methods=['POST'])
def upload_frame():
    """Получение нового кадра от клиента"""
    global last_frame
    try:
        frame_data = request.data
        with frame_lock:
            last_frame = frame_data
        return jsonify({'status': 'ok'})
    except:
        return jsonify({'status': 'error'}), 500

@app.route('/video/<name>')
def video(name):
    from flask import request as req
    video_path = VIDEOS / name
    
    if not video_path.exists():
        return "Video not found", 404
    
    # Поддержка range requests для видео
    range_header = req.headers.get('Range', None)
    if not range_header:
        return send_file(video_path, mimetype='video/mp4')
    
    import os
    size = os.path.getsize(video_path)
    byte_start = int(range_header.replace('bytes=', '').split('-')[0])
    byte_end = min(byte_start + 1024*1024, size-1)  # 1MB chunks
    
    def generate():
        with open(video_path, 'rb') as f:
            f.seek(byte_start)
            remaining = byte_end - byte_start + 1
            while remaining:
                chunk_size = min(8192, remaining)
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk
    
    return Response(
        generate(),
        206,  # Partial content
        headers={
            'Content-Range': f'bytes {byte_start}-{byte_end}/{size}',
            'Accept-Ranges': 'bytes',
            'Content-Length': str(byte_end - byte_start + 1),
            'Content-Type': 'video/mp4',
        }
    )

if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"  📹 СЕРВЕР ЗАПУЩЕН: http://localhost:6789")
    print(f"  🔴 LIVE: http://localhost:6789/live")
    print(f"  📁 Видео: {VIDEOS.absolute()}")
    print(f"  🎬 Файлов: {len(list(VIDEOS.glob('*.mp4')))}")
    print(f"{'='*60}\n")
    app.run(host='0.0.0.0', port=6789)
