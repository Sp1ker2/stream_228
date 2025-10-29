#!/usr/bin/env python3
"""Простой сервер с MJPEG стримом"""
from flask import Flask, Response, render_template_string
from pathlib import Path
import time
import threading

app = Flask(__name__)
VIDEOS = Path("temp_recordings")
VIDEOS.mkdir(exist_ok=True)

# Глобальная переменная для хранения последнего кадра
last_frame = None
frame_lock = threading.Lock()

@app.route('/')
def index():
    videos = sorted(VIDEOS.glob('*.mp4'), reverse=True)
    
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8">
    <title>📹 Screen Monitor</title>
    <style>
        body{{font-family:Arial;background:#f5f5f5;padding:30px;max-width:1400px;margin:0 auto}}
        h1{{color:#333}} 
        .video{{background:white;padding:20px;margin:15px 0;border-radius:10px}}
        .info{{color:#666;margin:10px 0}} 
        .live-btn{{
            background:#ff0000;color:white;padding:20px 40px;
            text-decoration:none;border-radius:10px;font-size:1.5em;font-weight:bold;
            display:inline-block;margin:30px 0;
            animation: pulse 2s infinite;
            box-shadow: 0 4px 15px rgba(255,0,0,0.3);
        }}
        @keyframes pulse {{0%,100%{{opacity:1;transform:scale(1)}} 50%{{opacity:0.8;transform:scale(1.05)}}}}
        .status{{background:#0f0;color:white;padding:10px;border-radius:5px;margin:10px 0}}
    </style>
    </head>
    <body>
        <h1>📹 Screen Monitor</h1>
        
        <div style="text-align:center">
            <a href="/live" class="live-btn">🔴 ПРЯМАЯ ТРАНСЛЯЦИЯ</a>
            <div class="status">● Запись активна</div>
        </div>
        
        <h2>📁 Записи ({len(videos)}):</h2>
    """
    
    for v in videos[:20]:  # Последние 20 видео
        mb = v.stat().st_size / (1024*1024)
        html += f"""
        <div class="video">
            <h3>{v.name}</h3>
            <div class="info">Размер: {mb:.2f} MB | {time.ctime(v.stat().st_mtime)}</div>
            <a href="/play/{v.name}" class="live-btn" style="background:#4CAF50;font-size:1em;padding:12px 25px">
                ▶️ СМОТРЕТЬ
            </a>
        </div>
        """
    
    html += "</body></html>"
    return html

@app.route('/live')
def live_view():
    """MJPEG трансляция"""
    html = """
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8">
    <title>🔴 LIVE Stream</title>
    <style>
        body{font-family:Arial;background:#000;padding:20px;margin:0}
        h1{color:white;text-align:center}
        .status{color:#0f0;text-align:center;font-size:1.5em;background:#000;padding:15px;border-radius:10px;margin:20px 0}
        #frame{display:block;margin:20px auto;max-width:100%;border:3px solid #0f0;border-radius:10px}
        .container{max-width:1400px;margin:0 auto}
    </style></head>
    <body>
        <div class="container">
            <h1>🔴 ПРЯМАЯ ТРАНСЛЯЦИЯ</h1>
            <div class="status" id="status">● LIVE</div>
            <img id="frame" src="/stream.mjpg" style="width:100%;max-width:100%">
            
            <script>
                let lastUpdate = Date.now();
                const img = document.getElementById('frame');
                const status = document.getElementById('status');
                
                function checkHealth() {
                    setTimeout(() => {
                        if (Date.now() - lastUpdate > 5000) {
                            status.textContent = '● Подключение...';
                            status.style.background = '#ff0';
                        } else {
                            status.textContent = '● LIVE';
                            status.style.background = '#0f0';
                        }
                        checkHealth();
                    }, 1000);
                }
                
                img.onload = function() {
                    lastUpdate = Date.now();
                };
                
                checkHealth();
            </script>
        </div>
    </body></html>
    """
    return html

@app.route('/stream.mjpg')
def stream_mjpg():
    """MJPEG stream"""
    def generate():
        global last_frame
        while True:
            with frame_lock:
                if last_frame:
                    yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + last_frame + b'\r\n'
                else:
                    # Черный кадр
                    yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\r\n'
            time.sleep(0.1)  # 10 FPS
    
    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/api/upload_frame', methods=['POST'])
def upload_frame():
    """Получение кадра от клиента"""
    global last_frame
    try:
        with frame_lock:
            last_frame = request.data
        return 'ok', 200
    except:
        return 'error', 500

@app.route('/play/<name>')
def play_video(name):
    """Страница просмотра видео"""
    video_path = VIDEOS / name
    if not video_path.exists():
        return "Video not found", 404
    
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8">
    <title>Просмотр: {name}</title>
    <style>
        body{{background:#000;margin:0;padding:20px}}
        video{{width:100%;max-height:90vh}}
        h2{{color:white}}
        a{{color:#0ff;text-decoration:none}}
    </style></head>
    <body>
        <a href="/">← Назад</a>
        <h2>{name}</h2>
        <video controls autoplay>
            <source src="/video/{name}" type="video/mp4">
        </video>
    </body></html>
    """
    return html

@app.route('/video/<name>')
def video(name):
    from flask import send_file
    return send_file(VIDEOS / name, mimetype='video/mp4')

if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"  📹 СЕРВЕР: http://localhost:6789")
    print(f"  🔴 LIVE: http://localhost:6789/live")
    print(f"{'='*60}\n")
    app.run(host='0.0.0.0', port=6789)





