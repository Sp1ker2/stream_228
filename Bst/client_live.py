"""
Screen Recording Client с прямой трансляцией
Записывает экран, отправляет live stream и сохраняет видео каждые 5 минут
"""
import cv2
import numpy as np
from PIL import ImageGrab
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
        self.machine_id = os.getenv('MACHINE_ID') or self.get_machine_id()
        self.server_ip = server_ip or os.getenv('SERVER_HOST', 'localhost')
        self.server_port = int(os.getenv('SERVER_PORT', '6789'))
        
        self.upload_interval = upload_interval
        self.is_recording = False
        self.current_video_file = None
        self.video_writer = None
        self.fps = 10
        self.frame_count = 0
        self.last_upload_time = time.time()
        self.is_streaming = True
        
        # Пишем в папку машины
        self.output_dir = Path("temp_recordings") / self.machine_id
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Проверяем, есть ли реальный экран для захвата
        self.is_docker = os.path.exists('/.dockerenv')
        self.use_simulated = self.is_docker or os.getenv('SIMULATE_SCREEN', '').lower() == 'true'
        
        # Поток для стрима
        self.streaming_thread = None
        
        logger.info(f"Screen Recorder initialized for machine: {self.machine_id}")
        logger.info(f"Server: http://{self.server_ip}:{self.server_port}")
        if self.use_simulated:
            logger.info("Using simulated screen (Docker mode)")
    
    def get_machine_id(self):
        """Получает ID машины из переменной окружения или генерирует"""
        env_id = os.getenv('MACHINE_ID')
        if env_id:
            return env_id
        try:
            hostname = socket.gethostname()
            try:
                user = os.getlogin()
                return f"{hostname}_{user}"
            except:
                return hostname
        except:
            return f"machine_{int(time.time())}"
    
    def get_screen_size(self):
        """Получает размер экрана или использует стандартный"""
        if self.use_simulated:
            return (1920, 1080)  # Стандартное разрешение для симуляции
        try:
            screenshot = ImageGrab.grab(all_screens=True)
            return screenshot.size
        except:
            return (1920, 1080)
    
    def start_recording(self):
        self.is_recording = True
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.machine_id}_{timestamp}.mp4"
        self.current_video_file = self.output_dir / filename
        
        screen_width, screen_height = self.get_screen_size()
        
        # Используем кодек H.264 для совместимости
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        if fourcc == -1:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        self.video_writer = cv2.VideoWriter(
            str(self.current_video_file),
            fourcc,
            self.fps,
            (screen_width, screen_height)
        )
        
        self.frame_count = 0
        logger.info(f"Started recording: {filename}")
    
    def stop_recording(self):
        self.is_recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        if self.current_video_file and self.current_video_file.exists():
            file_size = self.current_video_file.stat().st_size
            logger.info(f"Recording saved: {self.current_video_file.name} ({file_size/1024/1024:.2f} MB)")
            return self.current_video_file
        return None
    
    def capture_frame(self):
        """Захват кадра - реальный экран или симуляция"""
        if self.use_simulated:
            return self.generate_simulated_frame()
        try:
            screenshot = ImageGrab.grab(all_screens=True)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None
    
    def generate_simulated_frame(self):
        """Генерирует тестовый кадр с именем машины"""
        width, height = 1920, 1080
        frame = np.ones((height, width, 3), dtype=np.uint8) * 50  # Темный фон
        
        # Создаем цветной градиент
        for y in range(height):
            frame[y, :] = [50 + (y % 100) // 2, 80 + (y % 150) // 2, 100 + (y % 100) // 2]
        
        # Добавляем текст с именем машины
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 4
        thickness = 8
        text = f"{self.machine_id}"
        
        # Вычисляем размер текста для центрирования
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        x = (width - text_width) // 2
        y = (height + text_height) // 2
        
        # Тень текста
        cv2.putText(frame, text, (x + 5, y + 5), font, font_scale, (0, 0, 0), thickness)
        # Основной текст
        cv2.putText(frame, text, (x, y), font, font_scale, (0, 255, 255), thickness)
        
        # Добавляем время
        time_str = time.strftime("%Y-%m-%d %H:%M:%S")
        (tw, th), _ = cv2.getTextSize(time_str, font, 1.5, 3)
        cv2.putText(frame, time_str, (width - tw - 50, 50), font, 1.5, (255, 255, 255), 3)
        
        # Анимируем - меняем яркость по кадрам (создаем полный массив для добавления)
        frame_count_mod = (self.frame_count // 10) % 50
        brightness_shift = np.full((height, width, 3), 
                                    [frame_count_mod // 2, frame_count_mod // 3, frame_count_mod // 4], 
                                    dtype=np.uint8)
        frame = cv2.add(frame, brightness_shift)
        
        return frame
    
    def send_frame_for_stream(self, frame):
        """Отправка кадра для прямой трансляции"""
        try:
            # Кодируем кадр в JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            frame_bytes = buffer.tobytes()
            
            # Отправляем на сервер
            requests.post(
                f"http://{self.server_ip}:{self.server_port}/api/upload_frame?machine_id={self.machine_id}",
                data=frame_bytes,
                timeout=1,
                headers={'Content-Type': 'application/octet-stream', 'X-Machine-Id': self.machine_id}
            )
        except Exception as e:
            pass  # Тихий провал для стрима
    
    def record_segment(self, duration_seconds=300):
        """Записывает сегмент и отправляет кадры для стрима"""
        self.start_recording()
        
        start_time = time.time()
        frames_per_segment = self.fps * duration_seconds
        
        while self.is_recording and self.frame_count < frames_per_segment:
            frame = self.capture_frame()
            if frame is not None:
                # Сохраняем в видео
                self.video_writer.write(frame)
                self.frame_count += 1
                
                # Отправляем для стрима (каждый 2-й кадр для более плавного стрима)
                if self.is_streaming and self.frame_count % 2 == 0:
                    self.send_frame_for_stream(frame)
            
            time.sleep(1.0 / self.fps)
        
        video_file = self.stop_recording()
        return video_file
    
    def run(self):
        logger.info("=" * 60)
        logger.info("Starting Screen Recorder with LIVE STREAM")
        logger.info("=" * 60)
        logger.info(f"Machine ID: {self.machine_id}")
        logger.info(f"Server: http://{self.server_ip}:{self.server_port}")
        logger.info(f"Recording interval: {self.upload_interval} seconds")
        logger.info(f"LIVE Stream: http://{self.server_ip}:{self.server_port}/live/{self.machine_id}")
        logger.info(f"FPS: {self.fps}")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        try:
            while True:
                logger.info(f"Starting new recording segment...")
                video_file = self.record_segment(self.upload_interval)
                
                if video_file:
                    file_size = video_file.stat().st_size
                    logger.info(f"✅ Segment saved: {video_file.name} ({file_size/1024/1024:.2f} MB)")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\nStopping screen recorder...")
            if self.is_recording:
                self.stop_recording()
            logger.info("Screen recorder stopped")


def main():
    recorder = ScreenRecorder()
    recorder.run()


if __name__ == "__main__":
    main()

