"""
Screen Recording Client for Windows
Monitors user activity and uploads to server
"""

import cv2
import numpy as np
from PIL import ImageGrab
import time
import requests
import os
import json
import socket
import datetime
import threading
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScreenRecorder:
    def __init__(self, server_ip="195.133.17.131", upload_interval=60):
        self.server_ip = server_ip
        self.upload_interval = upload_interval  # seconds
        self.is_recording = False
        self.current_video_file = None
        self.video_writer = None
        self.fps = 6  # Lower FPS for Mac compatibility
        self.frame_count = 0
        self.last_upload_time = time.time()
        
        # Setup output directory
        self.output_dir = Path("temp_recordings")
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup log directory
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Get unique machine ID
        self.machine_id = self.get_machine_id()
        
        logger.info(f"Screen Recorder initialized for machine: {self.machine_id}")
        logger.info(f"Server: http://{self.server_ip}:5000")
    
    def get_machine_id(self):
        """Get unique machine identifier"""
        try:
            hostname = socket.gethostname()
            return f"{hostname}_{os.getlogin()}"
        except:
            return f"machine_{int(time.time())}"
    
    def get_screen_size(self):
        """Get current screen size"""
        screenshot = ImageGrab.grab(all_screens=True)
        return screenshot.size
    
    def start_recording(self):
        """Start recording screen"""
        self.is_recording = True
        
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.machine_id}_{timestamp}.mp4"
        self.current_video_file = self.output_dir / filename
        
        # Get screen resolution
        screen_width, screen_height = self.get_screen_size()
        
        # Setup video writer
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
        """Stop recording and save file"""
        self.is_recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        if self.current_video_file and self.current_video_file.exists():
            file_size = self.current_video_file.stat().st_size
            logger.info(f"Recording saved: {self.current_video_file.name} ({file_size/1024/1024:.2f} MB)")
            return self.current_video_file
        return None
    
    def capture_frame(self, bbox=None):
        """Capture single frame from screen"""
        try:
            # Grab screenshot - can capture specific screen with bbox
            screenshot = ImageGrab.grab(bbox=bbox, all_screens=True)
            
            # Convert to numpy array
            frame = np.array(screenshot)
            
            # Convert RGB to BGR (OpenCV format)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            return frame
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None
    
    def get_all_screens(self):
        """Get bounding boxes for all screens"""
        try:
            # This captures all screens including multiple monitors
            screenshot = ImageGrab.grab(all_screens=True)
            return screenshot.size  # Returns combined size
        except:
            # Fallback to single screen
            screenshot = ImageGrab.grab()
            return screenshot.size
    
    def record_segment(self, duration_seconds=60):
        """Record for specified duration"""
        self.start_recording()
        
        start_time = time.time()
        frames_per_segment = self.fps * duration_seconds
        
        while self.is_recording and self.frame_count < frames_per_segment:
            frame = self.capture_frame()
            if frame is not None:
                self.video_writer.write(frame)
                self.frame_count += 1
            
            # Control frame rate
            time.sleep(1.0 / self.fps)
        
        video_file = self.stop_recording()
        return video_file
    
    def upload_video(self, video_path):
        """Upload video to server with retry logic"""
        if not video_path or not video_path.exists():
            logger.warning("No video file to upload")
            return False
        
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Uploading {video_path.name} to server... (Attempt {attempt + 1}/{max_retries})")
                
                file_size = video_path.stat().st_size
                logger.info(f"File size: {file_size / (1024*1024):.2f} MB")
                
                # Read the video file
                with open(video_path, 'rb') as f:
                    files = {'video': (video_path.name, f, 'video/mp4')}
                    data = {
                        'machine_id': self.machine_id,
                        'timestamp': datetime.datetime.now().isoformat(),
                        'client_version': '1.0'
                    }
                    
                    # Upload to server with progress tracking
                    start_time = time.time()
                    response = requests.post(
                        f"http://{self.server_ip}:5000/upload",
                        files=files,
                        data=data,
                        timeout=600
                    )
                    
                    upload_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        logger.info(f"✓ Uploaded successfully: {video_path.name} in {upload_time:.1f}s")
                        # Delete local file after successful upload
                        try:
                            video_path.unlink()
                        except Exception as e:
                            logger.warning(f"Could not delete local file: {e}")
                        return True
                    else:
                        logger.error(f"✗ Upload failed: {response.status_code} - {response.text}")
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                        
                return False
                        
            except requests.exceptions.RequestException as e:
                logger.error(f"✗ Upload error: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
            except Exception as e:
                logger.error(f"✗ Unexpected error during upload: {e}")
                return False
        
        # If we get here, all retries failed
        logger.error("All upload attempts failed. Keeping local file.")
        return False
    
    def run(self):
        """Main recording loop"""
        logger.info("=" * 60)
        logger.info("Starting Screen Recorder")
        logger.info("=" * 60)
        logger.info(f"Machine ID: {self.machine_id}")
        logger.info(f"Server: http://{self.server_ip}:5000")
        logger.info(f"Recording interval: {self.upload_interval} seconds")
        logger.info(f"FPS: {self.fps}")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        consecutive_failures = 0
        max_failures = 3
        
        try:
            while True:
                try:
                    # Record a segment
                    logger.info(f"Starting new recording segment...")
                    video_file = self.record_segment(self.upload_interval)
                    
                    # Upload the segment
                    if video_file:
                        upload_success = self.upload_video(video_file)
                        if upload_success:
                            consecutive_failures = 0
                            self.last_upload_time = time.time()
                        else:
                            consecutive_failures += 1
                            logger.warning(f"Upload failures: {consecutive_failures}/{max_failures}")
                    else:
                        logger.error("Failed to record video segment")
                    
                    # If too many consecutive failures, wait longer before retry
                    if consecutive_failures >= max_failures:
                        logger.error("Too many consecutive failures. Waiting 60 seconds before retry...")
                        time.sleep(60)
                        consecutive_failures = 0
                    
                except Exception as e:
                    logger.error(f"Error in recording loop: {e}", exc_info=True)
                    time.sleep(10)  # Wait before retrying
                
                # Small delay before next recording
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\nStopping screen recorder...")
            if self.is_recording:
                self.stop_recording()
            logger.info("Screen recorder stopped")


def main():
    # Create recorder instance
    recorder = ScreenRecorder()
    
    # Start recording loop
    recorder.run()


if __name__ == "__main__":
    main()

