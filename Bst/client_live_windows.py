"""
Screen Recording Client для Windows
Записывает экран, отправляет live stream и сохраняет видео каждые 5 минут
ИСПОЛЬЗУЕТ mss для захвата экрана (лучше работает на Windows)
"""
import cv2
import numpy as np
from mss import mss  # Для Windows - быстрее и надежнее чем PIL
import time
import requests
import os
import socket
import datetime
import threading
from pathlib import Path
import logging
import base64

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScreenRecorder:
    def __init__(self, server_ip=None, upload_interval=300):  # 5 минут
        # Получаем из переменных окружения или используем значения по умолчанию
        self.machine_id = self.load_config_or_env('MACHINE_ID') or self.get_machine_id()
        self.server_ip = server_ip or self.load_config_or_env('SERVER_HOST') or 'localhost'
        self.server_port = int(self.load_config_or_env('SERVER_PORT') or '6789')
        
        self.upload_interval = upload_interval
        self.is_recording = False
        self.current_video_file = None
        self.video_writer = None
        self.fps = 10
        self.frame_count = 0
        self.last_upload_time = time.time()
        self.is_streaming = True
        
        # Пишем в папку машины (локально)
        self.output_dir = Path("temp_recordings") / self.machine_id
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Инициализируем mss для захвата экрана
        self.sct = mss()
        self.monitor = self.sct.monitors[1]  # Берем основной монитор
        
        # Поток для стрима
        self.streaming_thread = None
        
        logger.info(f"Screen Recorder initialized for machine: {self.machine_id}")
        logger.info(f"Server: http://{self.server_ip}:{self.server_port}")
        logger.info(f"Using mss for screen capture (Windows optimized)")
    
    def load_config_or_env(self, key):
        """Загружает значение из config.txt или переменной окружения"""
        # Сначала проверяем переменную окружения
        env_value = os.getenv(key)
        if env_value:
            return env_value
        
        # Затем проверяем config.txt
        config_file = Path("config.txt")
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            k, v = line.split('=', 1)
                            if k.strip() == key:
                                return v.strip()
            except Exception as e:
                logger.warning(f"Error reading config.txt: {e}")
        
        return None
    
    def get_machine_id(self):
        """Получает ID машины из конфигурации или генерирует"""
        try:
            hostname = socket.gethostname()
            try:
                user = os.getenv('USERNAME') or os.getenv('USER') or 'user'
                return f"{hostname}_{user}"
            except:
                return hostname
        except:
            return f"Windows_{int(time.time())}"
    
    def get_screen_size(self):
        """Получает размер экрана"""
        try:
            # Берем размер основного монитора из mss
            return (self.monitor['width'], self.monitor['height'])
        except:
            return (1920, 1080)
    
    def capture_screen(self):
        """Захватывает экран используя mss (быстро для Windows)"""
        try:
            # Захватываем экран используя mss
            screenshot = self.sct.grab(self.monitor)
            
            # Конвертируем mss.Screenshot в numpy array
            img = np.array(screenshot)
            
            # mss возвращает BGRA, конвертируем в RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
            
            return img
        except Exception as e:
            logger.error(f"Screen capture error: {e}")
            # Возвращаем черный кадр при ошибке
            width, height = self.get_screen_size()
            return np.zeros((height, width, 3), dtype=np.uint8)
    
    def send_frame_for_stream(self, frame):
        """Отправляет кадр на сервер для live стрима"""
        try:
            # Конвертируем frame в JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = buffer.tobytes()
            
            # Отправляем на сервер
            url = f"http://{self.server_ip}:{self.server_port}/api/upload_frame"
            headers = {
                'X-Machine-Id': self.machine_id,
                'Content-Type': 'application/octet-stream'
            }
            params = {
                'machine_id': self.machine_id
            }
            
            response = requests.post(
                url,
                data=frame_bytes,
                headers=headers,
                params=params,
                timeout=2
            )
            
            if response.status_code == 200:
                logger.debug(f"Frame sent successfully to {self.machine_id}")
            else:
                logger.warning(f"Failed to send frame: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending frame: {e}")
    
    def record_segment(self):
        """Записывает сегмент видео (5 минут)"""
        width, height = self.get_screen_size()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.machine_id}_{timestamp}.mp4"
        filepath = self.output_dir / filename
        
        # Используем кодек H.264 для совместимости с браузерами
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(str(filepath), fourcc, self.fps, (width, height))
        
        if not out.isOpened():
            logger.error(f"Failed to open video writer for {filepath}")
            return
        
        start_time = time.time()
        segment_duration = self.upload_interval  # 5 минут
        
        logger.info(f"Started recording segment: {filename}")
        
        while time.time() - start_time < segment_duration:
            if not self.is_recording:
                break
            
            frame = self.capture_screen()
            
            if frame is not None:
                # Записываем кадр в видео
                out.write(frame)
                
                # Отправляем каждый 2-й кадр для live стрима
                if self.is_streaming and self.frame_count % 2 == 0:
                    self.send_frame_for_stream(frame)
                
                self.frame_count += 1
            
            # Контроль FPS
            time.sleep(1.0 / self.fps)
        
        out.release()
        logger.info(f"Finished recording segment: {filename}")
        
        # Загружаем видео на сервер (опционально, если нужно)
        # Сейчас видео сохраняется только локально, на сервере только live стрим
    
    def start_recording(self):
        """Запускает запись в отдельном потоке"""
        if self.is_recording:
            logger.warning("Recording already started")
            return
        
        self.is_recording = True
        self.frame_count = 0
        
        def recording_loop():
            while self.is_recording:
                self.record_segment()
                if self.is_recording:  # Проверяем, не остановили ли нас
                    time.sleep(1)  # Небольшая пауза между сегментами
        
        recording_thread = threading.Thread(target=recording_loop, daemon=True)
        recording_thread.start()
        logger.info("Recording started")
    
    def stop_recording(self):
        """Останавливает запись"""
        self.is_recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        logger.info("Recording stopped")
    
    def run(self):
        """Основной цикл программы"""
        logger.info("Starting screen recorder...")
        self.start_recording()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping recorder...")
            self.stop_recording()
            logger.info("Recorder stopped")

if __name__ == "__main__":
    recorder = ScreenRecorder()
    recorder.run()

