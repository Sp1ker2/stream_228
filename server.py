from flask import Flask, send_from_directory, jsonify, request
from pathlib import Path
import os

app = Flask(__name__)
UPLOAD_DIR = Path("/root/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>📹 Screen Monitor</title>
        <style>
            body { font-family: Arial; background: #f5f5f5; padding: 20px; }
            .machine { background: white; padding: 20px; margin: 10px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .machine h2 { color: #333; }
            .video-list { display: flex; flex-wrap: wrap; gap: 15px; margin-top: 15px; }
            .video-item { background: #f9f9f9; padding: 15px; border-radius: 8px; }
            .btn { background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }
            .btn:hover { background: #45a049; }
            .info { color: #666; font-size: 0.9em; margin: 5px 0; }
        </style>
    </head>
    <body>
        <h1>📹 Screen Monitor Dashboard</h1>
        <div id="content">Загрузка...</div>
        
        <script>
        async function load() {
            const r = await fetch('/api/machines');
            const machines = await r.json();
            let html = '';
            for (let [id, data] of Object.entries(machines)) {
                html += `<div class="machine">
                    <h2>🖥️ ${id}</h2>
                    <div class="info">📁 Файлов: ${data.video_count}</div>
                    <div class="info">💾 Размер: ${(data.total_size/1024/1024).toFixed(2)} MB</div>
                    <div class="video-list">
                `;
                for (let video of data.videos) {
                    html += `
                        <div class="video-item">
                            <div class="info">📅 ${video.timestamp}</div>
                            <div class="info">📦 ${video.size_mb} MB</div>
                            <a href="${video.url}" target="_blank" class="btn">▶️ Смотреть</a>
                        </div>
                    `;
                }
                html += '</div></div>';
            }
            document.getElementById('content').innerHTML = html || '<p>Нет записей</p>';
        }
        load();
        setInterval(load, 5000);
        </script>
    </body>
    </html>
    """
    return html

@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    machine_id = request.form.get('machine_id', 'unknown')
    folder = UPLOAD_DIR / machine_id
    folder.mkdir(exist_ok=True)
    
    file = request.files['video']
    filename = f"{request.form.get('timestamp', 'now')}_{file.filename}"
    file.save(folder / filename)
    
    return jsonify({'status': 'ok'})

@app.route('/api/machines')
def machines():
    result = {}
    for folder in UPLOAD_DIR.iterdir():
        if folder.is_dir():
            videos = []
            for v in sorted(folder.glob('*.mp4'), reverse=True):
                videos.append({
                    'filename': v.name,
                    'url': f'/video/{folder.name}/{v.name}',
                    'timestamp': v.stat().st_mtime,
                    'size_mb': round(v.stat().st_size/1024/1024, 2)
                })
            if videos:
                result[folder.name] = {
                    'video_count': len(videos),
                    'total_size': sum(v.stat().st_size for v in folder.glob('*.mp4')),
                    'videos': videos[:10]
                }
    return jsonify(result)

@app.route('/video/<machine_id>/<filename>')
def video(machine_id, filename):
    return send_from_directory(f'{UPLOAD_DIR}/{machine_id}', filename, mimetype='video/mp4')

if __name__ == '__main__':
    print(f'🚀 Server: http://0.0.0.0:5000')
    app.run(host='0.0.0.0', port=5000, debug=False)
