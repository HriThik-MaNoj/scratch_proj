import unittest
import time
import os
import shutil
from pathlib import Path
from backend.video_handler import DashcamRecorder, VideoChunk

class TestDashcamRecorder(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_chunks"
        self.recorder = DashcamRecorder(
            chunk_duration=5,  # Shorter duration for testing
            resolution=(640, 480),
            fps=30,
            temp_dir=self.test_dir
        )

    def tearDown(self):
        self.recorder.cleanup()
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def test_recorder_initialization(self):
        """Test recorder initialization"""
        self.assertFalse(self.recorder.is_recording)
        self.assertEqual(self.recorder.current_chunk, 0)
        self.assertEqual(self.recorder.chunk_duration, 5)
        self.assertEqual(self.recorder.resolution, (640, 480))
        self.assertEqual(self.recorder.fps, 30)

    def test_start_stop_recording(self):
        """Test starting and stopping recording"""
        # Start recording
        success = self.recorder.start_recording()
        self.assertTrue(success)
        self.assertTrue(self.recorder.is_recording)
        
        # Let it record for a few seconds
        time.sleep(7)
        
        # Stop recording
        self.recorder.stop_recording()
        self.assertFalse(self.recorder.is_recording)

    def test_chunk_creation(self):
        """Test video chunk creation"""
        self.recorder.start_recording()
        time.sleep(7)  # Should create at least one chunk
        
        # Get a chunk
        chunk = self.recorder.get_next_chunk()
        self.recorder.stop_recording()
        
        # Verify chunk
        self.assertIsNotNone(chunk)
        self.assertIsInstance(chunk, VideoChunk)
        self.assertTrue(len(chunk.data) > 0)
        self.assertEqual(chunk.duration, 15)
        
        # Check metadata
        metadata = chunk.get_metadata()
        self.assertIn('start_time', metadata)
        self.assertIn('sequence_number', metadata)
        self.assertIn('duration', metadata)
        self.assertIn('timestamp', metadata)

    def test_cleanup(self):
        """Test cleanup functionality"""
        self.recorder.start_recording()
        time.sleep(7)
        self.recorder.stop_recording()
        
        # Verify cleanup
        self.assertFalse(self.recorder.is_recording)
        self.assertIsNone(self.recorder.capture)
        self.assertIsNone(self.recorder.writer)

    def test_get_status(self):
        """Test status reporting"""
        status = self.recorder.get_status()
        self.assertIn('is_recording', status)
        self.assertIn('current_chunk', status)
        self.assertIn('queue_size', status)
        self.assertIn('resolution', status)
        self.assertIn('fps', status)
        self.assertIn('chunk_duration', status)

if __name__ == '__main__':
    unittest.main()
