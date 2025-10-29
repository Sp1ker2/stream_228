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
    def __init__(self, server_ip="localhost", upload_interval=300):  # 5 минут
        self.server_ip = server_ip
        self.upload_interval = upload_interval
        self.is_recording = False
        self.current_video_file = None
        self.video_writer = None
        self.fps = 10
        self.frame_count = 0
        self.last_upload_time = time.time()
        self.is_streaming = True
        
        self.output_dir = Path("temp_recordings")
        self.output_dir.mkdir(exist_ok=True)
        
        self.machine_id = self.get_machine_id()
        
        # Поток для стрима
        self.streaming_thread = None
        
        logger.info(f"Screen Recorder initialized for machine: {self.machine_id}")
        logger.info(f"Server: http://{self.server_ip}:6789")
    
    def get_machine_id(self):
        try:
            hostname = socket.gethostname()
            return f"{hostname}_{os.getlogin()}"
        except:
            return f"machine_{int(time.time())}"
    
    def get_screen_size(self):
        screenshot = ImageGrab.grab(all_screens=True)
        return screenshot.size
    
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
        try:
            screenshot = ImageGrab.grab(all_screens=True)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None
    
    def send_frame_for_stream(self, frame):
        """Отправка кадра для прямой трансляции"""
        try:
            # Кодируем кадр в JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            frame_bytes = buffer.tobytes()
            
            # Отправляем на сервер
            requests.post(
                f"http://{self.server_ip}:6789/api/upload_frame",
                data=frame_bytes,
                timeout=1,
                headers={'Content-Type': 'application/octet-stream'}
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
                
                # Отправляем для стрима (каждый 10-й кадр)
                if self.is_streaming and self.frame_count % 10 == 0:
                    self.send_frame_for_stream(frame)
            
            time.sleep(1.0 / self.fps)
        
        video_file = self.stop_recording()
        return video_file
    
    def run(self):
        logger.info("=" * 60)
        logger.info("Starting Screen Recorder with LIVE STREAM")
        logger.info("=" * 60)
        logger.info(f"Machine ID: {self.machine_id}")
        logger.info(f"Server: http://{self.server_ip}:6789")
        logger.info(f"Recording interval: {self.upload_interval} seconds")
        logger.info(f"LIVE Stream: http://{self.server_ip}:6789/live")
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

