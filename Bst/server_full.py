"""
Screen Recording Server с полным веб-интерфейсом
"""

from flask import Flask, request, jsonify, send_from_directory, render_template_string
from pathlib import Path
import datetime
import os

app = Flask(__name__)

# Configuration
UPLOAD_DIR = Path("/root/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
SERVER_PORT = 5000

# HTML Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📹 Screen Monitor Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            color: white; text-align: center; margin-bottom: 30px;
            font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .machines-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px; margin-bottom: 30px;
        }
        .machine-card {
            background: white; border-radius: 15px; padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2); transition: transform 0.3s;
        }
        .machine-card:hover { transform: translateY(-5px); }
        .machine-header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 15px; padding-bottom: 15px; border-bottom: 2px solid #f0f0f0;
        }
        .machine-name { font-size: 1.3em; font-weight: bold; color: #333; }
        .machine-status {
            padding: 5px 15px; border-radius: 20px;
            font-size: 0.9em; font-weight: bold;
            background: #4CAF50; color: white;
        }
        .machine-info { color: #666; margin-bottom: 10px; }
        .view-btn {
            width: 100%; padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; border-radius: 8px;
            cursor: pointer; font-size: 1em; font-weight: bold;
            transition: transform 0.2s;
        }
        .view-btn:hover { transform: scale(1.05); }
        .modal {
            display: none; position: fixed; z-index: 1000;
            left: 0; top: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.9); overflow: auto;
        }
        .modal-content {
            background: white; margin: 30px auto; padding: 30px;
            border-radius: 15px; max-width: 95%; max-height: 90vh;
            overflow-y: auto;
        }
        .close {
            color: #aaa; float: right; font-size: 28px;
            font-weight: bold; cursor: pointer;
        }
        .close:hover { color: black; }
        .video-list {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px; margin-top: 20px;
        }
        .video-item {
            background: #f8f8f8; padding: 15px; border-radius: 10px;
            border: 1px solid #e0e0e0;
        }
        .video-title { font-weight: bold; margin-bottom: 10px; color: #333; }
        .video-info { font-size: 0.9em; color: #666; margin-bottom: 10px; }
        .video-btn {
            width: 100%; padding: 10px; background: #4CAF50;
            color: white; border: none; border-radius: 5px;
            cursor: pointer; font-weight: bold;
        }
        .video-btn:hover { background: #45a049; }
        .live-indicator {
            background: red; color: white; padding: 3px 10px;
            border-radius: 15px; font-size: 0.8em; font-weight: bold;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📹 Screen Monitor Dashboard</h1>
        <div id="machines-container" class="loading">Загрузка машин...</div>
    </div>

    <div id="videoModal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>
            <h2 id="modal-title"></h2>
            <div id="video-list"></div>
        </div>
    </div>

    <script>
        let machines = {};
        
        async function loadMachines() {
            try {
                const response = await fetch('/api/machines');
                machines = await response.json();
                displayMachines();
            } catch (error) {
                document.getElementById('machines-container').innerHTML = 
                    '<div class="loading">Ошибка загрузки</div>';
            }
        }
        
        function displayMachines() {
            const container = document.getElementById('machines-container');
            const machineIds = Object.keys(machines);
            
            if (machineIds.length === 0) {
                container.innerHTML = '<div class="loading">Нет подключенных машин</div>';
                return;
            }
            
            container.innerHTML = '<div class="machines-grid">' + 
                machineIds.map(machineId => `
                    <div class="machine-card">
                        <div class="machine-header">
                            <div class="machine-name">${machineId}</div>
                            <div class="machine-status">🟢 Активен</div>
                        </div>
                        <div class="machine-info">📁 ${machines[machineId].video_count} видео</div>
                        <div class="machine-info">📊 ${(machines[machineId].total_size / (1024*1024)).toFixed(2)} MB</div>
                        <button class="view-btn" onclick="viewVideos('${machineId}')">📺 Просмотр</button>
                    </div>
                `).join('') + '</div>';
        }
        
        async function viewVideos(machineId) {
            try {
                const response = await fetch(`/api/videos/${machineId}`);
                const videos = await response.json();
                
                document.getElementById('modal-title').textContent = `Записи: ${machineId}`;
                const videoList = document.getElementById('video-list');
                
                if (videos.length === 0) {
                    videoList.innerHTML = '<p>Нет видео</p>';
                } else {
                    videoList.innerHTML = videos.map(video => `
                        <div class="video-item">
                            <div class="video-title">${video.filename}</div>
                            <div class="video-info">📅 ${video.timestamp}</div>
                            <div class="video-info">📦 ${video.size_mb} MB</div>
                            <button class="video-btn" onclick="window.open('${video.url}', '_blank')">
                                ▶️ Смотреть
                            </button>
                        </div>
                    `).join('');
                }
                
                document.getElementById('videoModal').style.display = 'block';
            } catch (error) {
                alert('Ошибка загрузки видео');
            }
        }
        
        document.querySelector('.close').onclick = function() {
            document.getElementById('videoModal').style.display = 'none';
        }
        
        window.onclick = function(event) {
            const modal = document.getElementById('videoModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
        
        loadMachines();
        setInterval(loadMachines, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Прием видео файлов"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file'}), 400
        
        video = request.files['video']
        if video.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Получаем machine_id
        machine_id = request.form.get('machine_id', 'unknown')
        timestamp = request.form.get('timestamp', datetime.datetime.now().isoformat())
        
        # Создаем папку для машины
        machine_folder = UPLOAD_DIR / machine_id
        machine_folder.mkdir(exist_ok=True)
        
        # Сохраняем файл
        filename = f"{timestamp.replace(':', '-')}_{video.filename}"
        filepath = machine_folder / filename
        video.save(filepath)
        
        file_size = filepath.stat().st_size
        
        print(f"[UPLOAD] {machine_id}: {filename} ({file_size/(1024*1024):.2f} MB)")
        
        return jsonify({
            'status': 'success',
            'message': 'Файл загружен',
            'machine_id': machine_id,
            'filename': filename,
            'size_mb': round(file_size / (1024*1024), 2)
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/machines')
def api_machines():
    """API: список машин"""
    machines = {}
    
    if UPLOAD_DIR.exists():
        for machine_folder in UPLOAD_DIR.iterdir():
            if machine_folder.is_dir():
                machine_id = machine_folder.name
                videos = list(machine_folder.glob('*.mp4'))
                total_size = sum(video.stat().st_size for video in videos)
                
                machines[machine_id] = {
                    'video_count': len(videos),
                    'total_size': total_size,
                    'last_upload': max([v.stat().st_mtime for v in videos]).isoformat() if videos else None
                }
    
    return jsonify(machines)

@app.route('/api/videos/<machine_id>')
def api_videos(machine_id):
    """API: список видео для машины"""
    machine_folder = UPLOAD_DIR / machine_id
    
    if not machine_folder.exists():
        return jsonify([])
    
    videos = []
    for video_file in sorted(machine_folder.glob('*.mp4'), reverse=True):
        videos.append({
            'filename': video_file.name,
            'url': f'/video/{machine_id}/{video_file.name}',
            'timestamp': datetime.datetime.fromtimestamp(video_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
            'size_mb': round(video_file.stat().st_size / (1024 * 1024), 2)
        })
    
    return jsonify(videos)

@app.route('/video/<machine_id>/<filename>')
def serve_video(machine_id, filename):
    """Отдача видео файлов"""
    video_path = UPLOAD_DIR / machine_id / filename
    
    if not video_path.exists():
        return jsonify({'error': 'Video not found'}), 404
    
    return send_from_directory(str(video_path.parent), filename, mimetype='video/mp4')

if __name__ == '__main__':
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║          📹 Screen Recording Server                     ║
    ╠══════════════════════════════════════════════════════════╣
    ║  📊 Dashboard: http://195.133.17.131:5000                ║
    ║  📁 Upload Dir: {UPLOAD_DIR}                               ║
    ║  🚀 Server running on 0.0.0.0:{SERVER_PORT}                   ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=False)





