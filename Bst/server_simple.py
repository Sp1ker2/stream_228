#!/usr/bin/env python3
"""Простой сервер с MJPEG стримом"""
from flask import Flask, Response, render_template_string, request, send_file
from pathlib import Path
import time
import threading
import cv2
import shutil
import subprocess

app = Flask(__name__)
VIDEOS = Path("temp_recordings")
VIDEOS.mkdir(exist_ok=True)

# Кадры прямой трансляции по машинам
machine_id_to_last_frame = {}
machine_id_to_lock = {}

def get_machine_lock(machine_id: str) -> threading.Lock:
    if machine_id not in machine_id_to_lock:
        machine_id_to_lock[machine_id] = threading.Lock()
    return machine_id_to_lock[machine_id]

@app.route('/')
def index():
    # Список машин = подкаталоги, активные live-стримы и mp4 на верхнем уровне
    machines_dict = {}
    
    # Добавляем машины из папок
    for p in sorted(VIDEOS.iterdir(), key=lambda x: x.name):
        if p.is_dir() and not p.name.startswith('_'):
            count = len(list(p.glob('*.mp4')))
            size = sum(v.stat().st_size for v in p.glob('*.mp4'))
            machines_dict[p.name] = (count, size)
    
    # Добавляем активные live-стримы (даже если нет видео)
    for machine_id in machine_id_to_last_frame.keys():
        if machine_id and machine_id != 'default':
            if machine_id not in machines_dict:
                machines_dict[machine_id] = (0, 0)
            # Обновляем счетчики если есть папка
            folder = VIDEOS / machine_id
            if folder.exists():
                count = len(list(folder.glob('*.mp4')))
                size = sum(v.stat().st_size for v in folder.glob('*.mp4'))
                machines_dict[machine_id] = (count, size)
    
    # Файлы без папки считаем как Default
    root_videos = list(VIDEOS.glob('*.mp4'))
    if root_videos:
        size = sum(v.stat().st_size for v in root_videos)
        machines_dict["default"] = (len(root_videos), size)
    
    machines = [(k, machines_dict[k][0], machines_dict[k][1]) for k in sorted(machines_dict.keys())]
    
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
            <div class="status">● Запись активна</div>
        </div>
        
        <h2>🖥️ Машины ({len(machines)}):</h2>
    """
    for mid, count, size in machines:
        html += f"""
        <div class="video">
            <h3>🖥️ {mid}</h3>
            <div class="info">📁 Файлов: {count} | 💾 Размер: {size/1024/1024:.2f} MB</div>
            <a href="/live/{mid}" class="live-btn">🔴 LIVE</a>
            <a href="/list/{mid}" class="live-btn" style="background:#4CAF50">📼 Записи</a>
        </div>
        """
    
    html += "</body></html>"
    return html

@app.route('/live')
@app.route('/live/<machine_id>')
def live_view(machine_id: str = 'default'):
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
            <img id="frame" src="/stream.mjpg?machine_id={{ machine_id }}" style="width:100%;max-width:100%">
            
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
    return render_template_string(html, machine_id=machine_id)

@app.route('/stream.mjpg')
def stream_mjpg():
    """MJPEG stream - показывает последнее видео если нет live стрима"""
    machine_id = request.args.get('machine_id', 'default')

    def generate():
        lock = get_machine_lock(machine_id)
        last_frame = machine_id_to_last_frame.get(machine_id)
        # Если есть live кадр - используем его, иначе показываем последнее видео машины
        if last_frame:
            while True:
                with lock:
                    lf = machine_id_to_last_frame.get(machine_id)
                if lf:
                    yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + lf + b'\r\n'
                    time.sleep(0.1)  # 10 FPS
                else:
                    break
        else:
            # Показываем последнее записанное видео как слайдшоу
            folder = VIDEOS / machine_id if machine_id != 'default' else VIDEOS
            videos = sorted(folder.glob('*.mp4'), reverse=True)
            if videos:
                video_path = videos[0]
                cap = cv2.VideoCapture(str(video_path))
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Перематываем на начало
                        continue
                    
                    # Конвертируем в JPEG
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    frame_bytes = buffer.tobytes()
                    yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
                    time.sleep(1.0 / 6)  # 6 FPS как в оригинале
                
                cap.release()
            else:
                # Черный кадр если нет видео
                black_frame = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x01\x02\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xaa\xff\xd9'
                while True:
                    yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + black_frame + b'\r\n'
                    time.sleep(1)
    
    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/api/upload_frame', methods=['POST'])
def upload_frame():
    """Получение кадра от клиента"""
    machine_id = request.args.get('machine_id') or request.headers.get('X-Machine-Id') or 'default'
    try:
        # Создаем папку для машины если её нет (чтобы она появилась в списке)
        if machine_id != 'default':
            machine_folder = VIDEOS / machine_id
            machine_folder.mkdir(exist_ok=True, parents=True)
        
        lock = get_machine_lock(machine_id)
        with lock:
            machine_id_to_last_frame[machine_id] = request.data
        return 'ok', 200
    except Exception as e:
        print(f"[LIVE] upload_frame error for {machine_id}: {e}")
        return 'error', 500

@app.route('/list/<machine_id>')
def list_videos(machine_id: str):
    folder = VIDEOS / machine_id if machine_id != 'default' else VIDEOS
    videos = sorted(folder.glob('*.mp4'), reverse=True)
    html = """
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>Записи</title>
    <style>body{font-family:Arial;background:#f5f5f5;padding:30px;max-width:1400px;margin:0 auto}
    .video{background:white;padding:15px;margin:10px 0;border-radius:8px}</style></head><body>
    <h2>📼 Записи: %s</h2>
    <a href="/">← Назад</a>
    """ % machine_id
    for v in videos[:100]:
        mb = v.stat().st_size / (1024*1024)
        html += f"""
        <div class="video">
            <div><strong>{v.name}</strong> — {mb:.2f} MB</div>
            <a href="/play/{machine_id}/{v.name}">▶️ Смотреть</a>
        </div>
        """
    html += "</body></html>"
    return html

@app.route('/play/<machine_id>/<name>')
def play_video_machine(machine_id, name):
    """Страница просмотра видео"""
    folder = VIDEOS / machine_id if machine_id != 'default' else VIDEOS
    video_path = folder / name
    if not video_path.exists():
        return "Video not found", 404
    
    # Получаем информацию о видео
    mb = video_path.stat().st_size / (1024*1024)
    mtime = time.ctime(video_path.stat().st_mtime)
    
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8">
    <title>Просмотр: {name}</title>
    <style>
        body{{background:#1a1a1a;margin:0;padding:20px;font-family:Arial}}
        .container{{max-width:1400px;margin:0 auto}}
        h2{{color:white;margin:10px 0}}
        a{{color:#0ff;text-decoration:none;display:inline-block;margin-bottom:15px;padding:8px 15px;background:#333;border-radius:5px}}
        a:hover{{background:#444}}
        .info{{color:#aaa;margin:10px 0;font-size:0.9em}}
        video{{
            width:100%;
            max-height:85vh;
            background:#000;
            border-radius:8px;
        }}
        .controls{{
            margin-top:15px;
            color:white;
            padding:15px;
            background:#2a2a2a;
            border-radius:8px;
        }}
    </style></head>
    <body>
        <div class="container">
            <a href="/list/{machine_id}">← Назад к списку</a>
            <h2>📹 {name}</h2>
            <div class="info">💾 Размер: {mb:.2f} MB | 📅 {mtime}</div>
            <video controls autoplay preload="metadata" playsinline>
                <source src="/video/{machine_id}/{name}" type="video/mp4">
                Ваш браузер не поддерживает воспроизведение видео.
            </video>
            <div class="controls">
                <strong>Инструкция:</strong> Используйте кнопки управления для воспроизведения видео.
                <br>
                <strong>Отладка:</strong>
                <a href="/video/{machine_id}/{name}" style="color:#4CAF50" download>📥 Скачать видео</a> | 
                <a href="/test/{machine_id}/{name}" style="color:#ff0">🧪 Тест воспроизведения</a>
            </div>
            <script>
                const video = document.querySelector('video');
                video.addEventListener('error', function(e) {{
                    console.error('Video error:', video.error);
                    alert('Ошибка воспроизведения: ' + (video.error ? video.error.message : 'Неизвестная ошибка'));
                }});
                video.addEventListener('loadeddata', function() {{
                    console.log('Video loaded! Duration:', video.duration);
                }});
            </script>
        </div>
    </body></html>
    """
    return html

@app.route('/video/<machine_id>/<name>')
def video(machine_id, name):
    """Отдача видео. Если браузер не может воспроизвести, пробуем транскодировать в H.264 (ffmpeg)."""
    folder = VIDEOS / machine_id if machine_id != 'default' else VIDEOS
    video_path = folder / name
    if not video_path.exists():
        return "Video not found", 404

    # Кэш для перекодированных файлов
    cache_dir = folder / "_h264_cache"
    cache_dir.mkdir(exist_ok=True)
    cached_path = cache_dir / name

    # Если уже перекодировано ранее — отдаем кэш
    if cached_path.exists() and cached_path.stat().st_size > 0:
        print(f"[VIDEO] Отдаю конвертированное видео: {name} ({cached_path.stat().st_size/1024/1024:.2f} MB)")
        return send_file(
            str(cached_path),
            mimetype='video/mp4',
            as_attachment=False,
            conditional=True
        )

    # Если есть ffmpeg — попробуем перекодировать в совместимый формат
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg:
        try:
            print(f"[CONVERT] Начинаю конвертацию {name}...")
            # Быстрая перекодировка с moov в начале файла (faststart)
            cmd = [
                ffmpeg,
                '-y',
                '-i', str(video_path),
                '-c:v', 'libx264',
                '-preset', 'veryfast',
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',
                '-an',  # без звука
                str(cached_path)
            ]
            result = subprocess.run(
                cmd, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                timeout=300
            )
            print(f"[CONVERT] Конвертация завершена: {cached_path.stat().st_size/1024/1024:.2f} MB")
            
            if cached_path.exists() and cached_path.stat().st_size > 0:
                return send_file(
                    str(cached_path),
                    mimetype='video/mp4',
                    as_attachment=False,
                    conditional=True
                )
            else:
                print(f"[CONVERT] Ошибка: файл не создан")
        except subprocess.TimeoutExpired:
            print(f"[CONVERT] Таймаут при конвертации {name}")
        except subprocess.CalledProcessError as e:
            print(f"[CONVERT] Ошибка конвертации {name}: {e.stderr.decode()[:200]}")
        except Exception as e:
            print(f"[CONVERT] Неожиданная ошибка: {e}")
    else:
        # ffmpeg не найден - используем OpenCV для конвертации (медленно, но работает)
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise Exception("Cannot open video")
            
            # Получаем параметры видео
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 6
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Пробуем использовать H.264 кодек
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            if fourcc == -1:
                fourcc = cv2.VideoWriter_fourcc(*'H264')
            if fourcc == -1:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Fallback
            
            out = cv2.VideoWriter(str(cached_path), fourcc, fps, (width, height))
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
                frame_count += 1
                
                # Ограничиваем размер во избежание зависания
                if frame_count > 10000:
                    break
            
            cap.release()
            out.release()
            
            if cached_path.exists() and cached_path.stat().st_size > 0:
                return send_file(
                    str(cached_path),
                    mimetype='video/mp4',
                    as_attachment=False,
                    conditional=True
                )
        except Exception as e:
            print(f"OpenCV conversion failed: {e}")

    # Отдаем оригинал только если конвертация не удалась (может не воспроизвестись в некоторых браузерах)
    print(f"[VIDEO] Отдаю оригинальное видео (не конвертировано): {name}")
    return send_file(
        str(video_path),
        mimetype='video/mp4',
        as_attachment=False,
        conditional=True
    )

@app.route('/test/<machine_id>/<name>')
def test_video(machine_id, name):
    """Тестовая страница для проверки видео"""
    folder = VIDEOS / machine_id if machine_id != 'default' else VIDEOS
    video_path = folder / name
    cache_dir = folder / "_h264_cache"
    cached_path = cache_dir / name
    
    has_original = video_path.exists()
    has_converted = cached_path.exists() and cached_path.stat().st_size > 0
    
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8">
    <title>Тест: {name}</title>
    <style>
        body{{background:#1a1a1a;color:white;padding:20px;font-family:monospace}}
        .info{{margin:10px 0;padding:10px;background:#2a2a2a;border-radius:5px}}
        .ok{{color:#0f0}}
        .error{{color:#f00}}
        video{{width:100%;max-height:70vh;background:#000;margin:20px 0}}
    </style></head>
    <body>
        <h2>🧪 Тест воспроизведения: {name}</h2>
        <div class="info">
            Оригинал: {'✅ есть' if has_original else '❌ нет'} 
            ({video_path.stat().st_size/1024/1024:.2f} MB)<br>
            Конвертировано: {'✅ есть' if has_converted else '❌ нет'}
            {f'({cached_path.stat().st_size/1024/1024:.2f} MB)' if has_converted else ''}
        </div>
        <video controls autoplay>
            <source src="/video/{machine_id}/{name}" type="video/mp4">
        </video>
        <div class="info">
            Откройте консоль браузера (F12) чтобы увидеть ошибки
        </div>
        <script>
            const video = document.querySelector('video');
            video.addEventListener('error', (e) => {{
                document.body.innerHTML += '<div class="error">❌ ОШИБКА: ' + video.error.message + '</div>';
            }});
            video.addEventListener('loadeddata', () => {{
                document.body.innerHTML += '<div class="ok">✅ Видео загружено! Длительность: ' + video.duration + ' сек</div>';
            }});
        </script>
    </body></html>
    """
    return html

if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"  📹 СЕРВЕР: http://localhost:6789")
    print(f"  🔴 LIVE: http://localhost:6789/live")
    print(f"{'='*60}\n")
    app.run(host='0.0.0.0', port=6789)





