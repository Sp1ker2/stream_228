#!/usr/bin/env python3
"""Простой сервер для просмотра видео"""
from flask import Flask, send_file, jsonify
from pathlib import Path
import os

app = Flask(__name__)

# Используем локальную папку с видео
VIDEOS_DIR = Path("temp_recordings")
VIDEOS_DIR.mkdir(exist_ok=True)

@app.route('/')
def index():
    html = '''
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>📹 Screen Monitor</title>
    <style>
        body{font-family:Arial;background:#f5f5f5;padding:20px;max-width:1200px;margin:0 auto}
        .video-card{background:white;padding:20px;margin:15px 0;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
        h1{color:#333}
        .video-item{display:inline-block;margin:10px;padding:15px;background:#f9f9f9;border-radius:8px}
        .btn{background:#4CAF50;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;display:inline-block;margin-top:10px}
        .info{color:#666;font-size:0.9em;margin:5px 0}
    </style></head>
    <body>
        <h1>📹 Screen Monitor - Ваши записи</h1>
        <div id="videos"></div>
        <script>
        fetch('/api/videos').then(r=>r.json()).then(videos=>{
            let html = '';
            videos.forEach(v=>{
                const mb = (v.size/1024/1024).toFixed(2);
                html += `<div class="video-item">
                    <div class="info">📅 ${v.date}</div>
                    <div class="info">📦 ${mb} MB</div>
                    <a href="/video/${v.name}" target="_blank" class="btn">▶️ Смотреть</a>
                </div>`;
            });
            document.getElementById('videos').innerHTML = html || '<p>Нет записей</p>';
        });
        </script>
    </body></html>
    '''
    return html

@app.route('/api/videos')
def api_videos():
    videos = []
    if VIDEOS_DIR.exists():
        for f in sorted(VIDEOS_DIR.glob('*.mp4'), reverse=True):
            stat = f.stat()
            videos.append({
                'name': f.name,
                'size': stat.st_size,
                'date': f.stat().st_mtime
            })
    return jsonify(videos)

@app.route('/video/<filename>')
def serve_video(filename):
    video_path = VIDEOS_DIR / filename
    if video_path.exists():
        return send_file(video_path, mimetype='video/mp4')
    return "Not found", 404

if __name__ == '__main__':
    print("🚀 Server: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)





