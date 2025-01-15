#!/usr/bin/env python3

import cv2
import time
import threading
import queue
import logging
import os
import numpy as np
from datetime import datetime
from typing import Optional, Generator, Dict
from pathlib import Path

class VideoChunk:
    def __init__(self, start_time: float, data: bytes, sequence_number: int, metadata: Dict = None):
        """
        Initialize a video chunk
        Args:
            start_time: Start time of the chunk in seconds
            data: Raw video data
            sequence_number: Sequence number of the chunk
            metadata: Additional metadata for the chunk
        """
        self.start_time = start_time
        self.data = data
        self.sequence_number = sequence_number
        self._metadata = metadata or {}
        self.timestamp = datetime.fromtimestamp(start_time)
        
    def get_metadata(self) -> Dict:
        """Get chunk metadata"""
        metadata = {
            'timestamp': self.timestamp.isoformat(),
            'sequence_number': self.sequence_number,
            'start_time': self.start_time,
            **self._metadata  # Include any additional metadata
        }
        return metadata

class DashcamRecorder:
    def __init__(self, 
                 chunk_duration: int = 30,
                 resolution: tuple = (1280, 720),  
                 fps: int = 30,
                 temp_dir: str = "temp_chunks",
                 test_mode: bool = True):  
        """
        Initialize the dashcam recorder
        
        Args:
            chunk_duration: Duration of each video chunk in seconds
            resolution: Video resolution (width, height)
            fps: Frames per second
            temp_dir: Directory to store temporary chunks
            test_mode: If True, generate synthetic video instead of using camera
        """
        self.logger = logging.getLogger(__name__)
        self.chunk_duration = chunk_duration
        self.resolution = resolution
        self.fps = fps
        self.temp_dir = Path(temp_dir)
        self.test_mode = test_mode
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize state
        self.is_recording = False
        self.current_chunk = 0
        self.capture = None
        self.writer = None
        self.chunk_queue = queue.Queue(maxsize=30)  
        self.record_thread = None
        self.chunk_thread = None
        
        # Preview frame
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        
        # Video configuration
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.frame_size = (int(resolution[0]), int(resolution[1]))

    def _generate_test_frame(self, frame_number: int) -> np.ndarray:
        """Generate a test frame with timestamp and moving elements"""
        # Create a blank frame
        frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Add frame number
        cv2.putText(frame, f"Frame: {frame_number}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Add moving element
        radius = 20
        center_x = int(self.resolution[0]/2 + radius * np.cos(frame_number/10))
        center_y = int(self.resolution[1]/2 + radius * np.sin(frame_number/10))
        cv2.circle(frame, (center_x, center_y), 30, (0, 0, 255), -1)
        
        return frame

    def start_recording(self) -> bool:
        """Start the recording process"""
        if self.is_recording:
            self.logger.warning("Recording is already in progress")
            return False

        try:
            if self.test_mode:
                self.logger.info("Starting in test mode with synthetic video")
                self.is_recording = True
                self.current_chunk = 0
                self.record_thread = threading.Thread(target=self._record_loop)
                self.chunk_thread = threading.Thread(target=self._chunk_management_loop)
                self.record_thread.start()
                self.chunk_thread.start()
                return True

            # Try different camera indices
            camera_found = False
            for camera_index in range(4):  # Try first 4 camera indices
                self.logger.info(f"Trying camera index {camera_index}")
                self.capture = cv2.VideoCapture(camera_index)
                if self.capture.isOpened():
                    camera_found = True
                    self.logger.info(f"Successfully opened camera {camera_index}")
                    break
                self.capture.release()

            if not camera_found:
                raise RuntimeError("No available camera found. Please check camera connections.")

            # Set camera properties
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)

            # Verify camera settings
            actual_width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.capture.get(cv2.CAP_PROP_FPS)

            self.logger.info(f"Camera initialized with resolution: {actual_width}x{actual_height}, FPS: {actual_fps}")

            # Create output directory if it doesn't exist
            os.makedirs(str(self.temp_dir), exist_ok=True)

            # Start recording thread
            self.is_recording = True
            self.current_chunk = 0
            self.record_thread = threading.Thread(target=self._record_loop)
            self.chunk_thread = threading.Thread(target=self._chunk_management_loop)
            self.record_thread.start()
            self.chunk_thread.start()

            return True

        except Exception as e:
            self.logger.error(f"Failed to start recording: {str(e)}")
            if self.capture:
                self.capture.release()
                self.capture = None
            self.is_recording = False
            raise RuntimeError(f"Failed to start recording: {str(e)}")

    def stop_recording(self) -> None:
        """Stop the recording process"""
        self.is_recording = False
        if self.record_thread:
            self.record_thread.join()
        if self.chunk_thread:
            self.chunk_thread.join()
        self.cleanup()
        self.logger.info("Stopped recording")

    def _record_loop(self) -> None:
        """Main recording loop"""
        try:
            start_time = time.time()
            frames = []
            frame_count = 0
            
            while self.is_recording:
                if self.test_mode:
                    frame = self._generate_test_frame(frame_count)
                    frame_count += 1
                    ret = True
                else:
                    ret, frame = self.capture.read()
                
                if not ret:
                    self.logger.error("Failed to get frame")
                    continue

                # Update preview frame
                with self.frame_lock:
                    self.latest_frame = frame.copy()

                frames.append(frame)
                
                # Check if it's time to create a new chunk
                elapsed = time.time() - start_time
                if elapsed >= self.chunk_duration:
                    if frames:
                        try:
                            # Create chunk file
                            chunk_path = self.temp_dir / f"chunk_{self.current_chunk}.mp4"
                            writer = cv2.VideoWriter(
                                str(chunk_path),
                                self.fourcc,
                                self.fps,
                                self.frame_size
                            )
                            
                            # Write frames to chunk
                            for f in frames:
                                writer.write(f)
                            writer.release()
                            
                            # Create chunk object
                            with open(chunk_path, 'rb') as f:
                                chunk_data = f.read()
                            
                            chunk = VideoChunk(
                                start_time=start_time,
                                data=chunk_data,
                                sequence_number=self.current_chunk,
                                metadata={
                                    'frame_count': len(frames),
                                    'fps': self.fps,
                                    'resolution': self.resolution,
                                    'test_mode': self.test_mode
                                }
                            )
                            
                            # Add to queue
                            self.chunk_queue.put(chunk)
                            self.current_chunk += 1
                            
                        except Exception as e:
                            self.logger.error(f"Error creating chunk: {e}")
                            
                    # Reset for next chunk
                    frames = []
                    start_time = time.time()
                
                # Control frame rate
                time.sleep(1/self.fps)
                
        except Exception as e:
            self.logger.error(f"Recording loop error: {e}")
            self.is_recording = False

    def _save_chunk(self, frames: list, start_time: float) -> Optional[str]:
        """Save frames as a video chunk"""
        try:
            chunk_path = self.temp_dir / f"chunk_{self.current_chunk}_{int(start_time)}.mp4"
            
            # Create writer with proper codec
            writer = cv2.VideoWriter(
                str(chunk_path),
                self.fourcc,
                self.fps,
                self.frame_size,
                True  
            )
            
            if not writer.isOpened():
                raise RuntimeError("Failed to initialize video writer")

            # Write frames with error checking
            for frame in frames:
                if frame is not None:
                    writer.write(frame)

            writer.release()
            
            # Verify the file was created and has content
            if not chunk_path.exists() or chunk_path.stat().st_size == 0:
                raise RuntimeError("Failed to create video chunk")
                
            return str(chunk_path)

        except Exception as e:
            self.logger.error(f"Failed to save chunk: {str(e)}")
            if chunk_path.exists():
                try:
                    chunk_path.unlink()
                except:
                    pass
            return None

    def _chunk_management_loop(self) -> None:
        """Manage chunks and cleanup old files"""
        while self.is_recording or not self.chunk_queue.empty():
            try:
                # Cleanup old chunks
                self._cleanup_old_chunks()
                time.sleep(1)  
            except Exception as e:
                self.logger.error(f"Error in chunk management: {str(e)}")

    def _cleanup_old_chunks(self) -> None:
        """Clean up old chunk files"""
        try:
            current_time = time.time()
            for chunk_file in self.temp_dir.glob("chunk_*.mp4"):
                # Only delete files older than 5 minutes and not in the queue
                if current_time - chunk_file.stat().st_mtime > 300:
                    chunk_number = int(chunk_file.stem.split('_')[1])
                    if not any(chunk.sequence_number == chunk_number 
                             for chunk in list(self.chunk_queue.queue)):
                        chunk_file.unlink()
        except Exception as e:
            self.logger.error(f"Error cleaning up chunks: {str(e)}")

    def _add_timestamp(self, frame: np.ndarray) -> np.ndarray:
        """Add timestamp overlay to frame"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Create a copy to avoid modifying original
        frame_with_overlay = frame.copy()
        
        # Get frame dimensions
        height, width = frame_with_overlay.shape[:2]
        
        # Configure text properties
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = min(width, height) / 1000.0  
        thickness = max(1, int(font_scale * 2))
        color = (255, 255, 255)  
        
        # Add black background for better readability
        text_size = cv2.getTextSize(timestamp, font, font_scale, thickness)[0]
        padding = 10
        
        # Draw background rectangle
        cv2.rectangle(
            frame_with_overlay,
            (width - text_size[0] - padding * 2, height - text_size[1] - padding * 2),
            (width - padding, height - padding),
            (0, 0, 0),
            -1
        )
        
        # Add timestamp text
        cv2.putText(
            frame_with_overlay,
            timestamp,
            (width - text_size[0] - padding, height - padding - 5),
            font,
            font_scale,
            color,
            thickness
        )
        
        # Add GPS coordinates if available
        if hasattr(self, 'gps_coords'):
            gps_text = f"GPS: {self.gps_coords}"
            gps_size = cv2.getTextSize(gps_text, font, font_scale * 0.8, thickness)[0]
            
            # Draw background for GPS
            cv2.rectangle(
                frame_with_overlay,
                (width - gps_size[0] - padding * 2, height - text_size[1] - gps_size[1] - padding * 4),
                (width - padding, height - text_size[1] - padding * 2),
                (0, 0, 0),
                -1
            )
            
            # Add GPS text
            cv2.putText(
                frame_with_overlay,
                gps_text,
                (width - gps_size[0] - padding, height - text_size[1] - padding * 2 - 5),
                font,
                font_scale * 0.8,
                color,
                thickness
            )
        
        return frame_with_overlay

    def get_next_chunk(self) -> Optional[VideoChunk]:
        """Get the next available video chunk"""
        try:
            return self.chunk_queue.get_nowait()
        except queue.Empty:
            return None

    def get_preview_frame(self) -> Optional[np.ndarray]:
        """Get the latest preview frame with timestamp overlay"""
        with self.frame_lock:
            if self.latest_frame is not None:
                return self._add_timestamp(self.latest_frame)
        return None

    def cleanup(self) -> None:
        """Clean up resources"""
        if self.capture:
            self.capture.release()
        if self.writer:
            self.writer.release()
        cv2.destroyAllWindows()

    def get_status(self) -> Dict:
        """Get current recording status"""
        return {
            "is_recording": self.is_recording,
            "current_chunk": self.current_chunk,
            "queue_size": self.chunk_queue.qsize(),
            "resolution": self.resolution,
            "fps": self.fps,
            "chunk_duration": self.chunk_duration
        }
