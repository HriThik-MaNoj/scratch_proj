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
    def __init__(self, start_time: float, data: bytes, sequence_number: int):
        self.start_time = start_time
        self.data = data
        self.sequence_number = sequence_number
        self.duration = 15  # seconds
        self.timestamp = datetime.fromtimestamp(start_time)

    def get_metadata(self) -> Dict:
        return {
            "start_time": self.start_time,
            "sequence_number": self.sequence_number,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat()
        }

class DashcamRecorder:
    def __init__(self, 
                 chunk_duration: int = 15,
                 resolution: tuple = (1920, 1080),
                 fps: int = 30,
                 temp_dir: str = "temp_chunks"):
        """
        Initialize the dashcam recorder
        
        Args:
            chunk_duration: Duration of each video chunk in seconds
            resolution: Video resolution (width, height)
            fps: Frames per second
            temp_dir: Directory to store temporary chunks
        """
        self.logger = logging.getLogger(__name__)
        self.chunk_duration = chunk_duration
        self.resolution = resolution
        self.fps = fps
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize state
        self.is_recording = False
        self.current_chunk = 0
        self.capture: Optional[cv2.VideoCapture] = None
        self.writer: Optional[cv2.VideoWriter] = None
        self.chunk_queue = queue.Queue(maxsize=30)  # Buffer for 30 chunks max
        self.record_thread: Optional[threading.Thread] = None
        self.chunk_thread: Optional[threading.Thread] = None
        
        # Preview frame
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        
        # Video configuration
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.frame_size = (int(resolution[0]), int(resolution[1]))

    def start_recording(self) -> bool:
        """Start the recording process"""
        if self.is_recording:
            self.logger.warning("Recording is already in progress")
            return False

        try:
            self.capture = cv2.VideoCapture(0)
            if not self.capture.isOpened():
                raise RuntimeError("Failed to open camera")

            # Set camera properties
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)

            self.is_recording = True
            self.current_chunk = 0

            # Start recording thread
            self.record_thread = threading.Thread(target=self._record_loop)
            self.chunk_thread = threading.Thread(target=self._chunk_management_loop)
            self.record_thread.start()
            self.chunk_thread.start()

            self.logger.info("Started recording")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start recording: {str(e)}")
            self.cleanup()
            return False

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
        chunk_start_time = time.time()
        frames = []
        
        while self.is_recording:
            try:
                ret, frame = self.capture.read()
                if not ret:
                    self.logger.error("Failed to capture frame")
                    continue

                # Add timestamp overlay
                frame_with_overlay = self._add_timestamp(frame)

                # Update preview frame
                with self.frame_lock:
                    self.latest_frame = frame.copy()

                # Store frame with overlay for recording
                frames.append(frame_with_overlay)
                elapsed_time = time.time() - chunk_start_time

                # Check if chunk duration is reached
                if elapsed_time >= self.chunk_duration:
                    # Create new chunk
                    chunk_path = self._save_chunk(frames, chunk_start_time)
                    if chunk_path:
                        with open(chunk_path, 'rb') as f:
                            chunk_data = f.read()
                        
                        # Create chunk object and add to queue
                        chunk = VideoChunk(
                            start_time=chunk_start_time,
                            data=chunk_data,
                            sequence_number=self.current_chunk
                        )
                        self.chunk_queue.put(chunk)
                        self.current_chunk += 1

                    # Reset for next chunk
                    frames = []
                    chunk_start_time = time.time()

            except Exception as e:
                self.logger.error(f"Error in recording loop: {str(e)}")
                break

    def _save_chunk(self, frames: list, start_time: float) -> Optional[str]:
        """Save frames as a video chunk"""
        try:
            chunk_path = self.temp_dir / f"chunk_{self.current_chunk}_{int(start_time)}.mp4"
            writer = cv2.VideoWriter(
                str(chunk_path),
                self.fourcc,
                self.fps,
                self.frame_size
            )

            for frame in frames:
                writer.write(frame)

            writer.release()
            return str(chunk_path)

        except Exception as e:
            self.logger.error(f"Failed to save chunk: {str(e)}")
            return None

    def _chunk_management_loop(self) -> None:
        """Manage chunks and cleanup old files"""
        while self.is_recording or not self.chunk_queue.empty():
            try:
                # Cleanup old chunks
                self._cleanup_old_chunks()
                time.sleep(1)  # Check every second
            except Exception as e:
                self.logger.error(f"Error in chunk management: {str(e)}")

    def _cleanup_old_chunks(self) -> None:
        """Clean up old chunk files"""
        try:
            current_time = time.time()
            for chunk_file in self.temp_dir.glob("chunk_*.mp4"):
                # Keep files for 5 minutes
                if current_time - chunk_file.stat().st_mtime > 300:
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
        font_scale = min(width, height) / 1000.0  # Scale based on frame size
        thickness = max(1, int(font_scale * 2))
        color = (255, 255, 255)  # White text
        
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
