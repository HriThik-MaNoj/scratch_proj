#!/usr/bin/env python3

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from queue import Queue
from datetime import datetime

from backend.dashcam_manager import DashcamManager
from backend.video_handler import VideoChunk
from backend.ipfs_handler import IPFSHandler
from backend.blockchain_handler import BlockchainHandler
from backend.batch_processor import BatchProcessor

@pytest.fixture
def mock_components():
    """Create mock components for testing"""
    with patch('backend.dashcam_manager.DashcamRecorder') as mock_recorder, \
         patch('backend.dashcam_manager.IPFSHandler') as mock_ipfs, \
         patch('backend.dashcam_manager.BlockchainHandler') as mock_blockchain, \
         patch('backend.dashcam_manager.BatchProcessor') as mock_processor:
        
        # Configure recorder mock
        recorder_instance = mock_recorder.return_value
        recorder_instance.chunk_queue = Queue()
        recorder_instance.is_recording = False
        recorder_instance.start_recording.return_value = True
        recorder_instance.get_status.return_value = {
            'is_recording': False,
            'current_chunk': 0,
            'queue_size': 0
        }
        
        # Configure blockchain mock
        blockchain_instance = mock_blockchain.return_value
        blockchain_instance.start_video_session.return_value = 1
        blockchain_instance.is_session_active.return_value = True
        
        # Configure batch processor mock
        processor_instance = mock_processor.return_value
        processor_instance.get_stats.return_value = {
            'total_processed': 0,
            'successful_uploads': 0,
            'failed_uploads': 0
        }
        
        yield {
            'recorder': recorder_instance,
            'ipfs': mock_ipfs.return_value,
            'blockchain': blockchain_instance,
            'processor': processor_instance
        }

@pytest.fixture
def manager(mock_components):
    """Create DashcamManager instance with mock components"""
    return DashcamManager()

def create_mock_chunk(sequence_number: int = 0) -> Mock:
    """Create a mock video chunk"""
    chunk = Mock(spec=VideoChunk)
    chunk.sequence_number = sequence_number
    chunk.start_time = time.time()
    chunk.timestamp = datetime.fromtimestamp(chunk.start_time)
    chunk.data = b'mock_video_data'
    chunk.get_metadata.return_value = {
        'sequence_number': sequence_number,
        'start_time': chunk.start_time,
        'timestamp': chunk.timestamp.isoformat()
    }
    return chunk

class TestDashcamManager:
    def test_initialization(self, manager, mock_components):
        """Test manager initialization"""
        assert manager is not None
        assert manager.session_id is None
        assert not manager.is_recording
        assert manager.upload_thread is None

    def test_start_recording_success(self, manager, mock_components):
        """Test successful recording start"""
        success = manager.start_recording()
        
        assert success
        assert manager.is_recording
        assert manager.session_id == 1
        assert manager.upload_thread is not None
        assert manager.upload_thread.is_alive()
        
        mock_components['recorder'].start_recording.assert_called_once()
        mock_components['blockchain'].start_video_session.assert_called_once()
        mock_components['processor'].start.assert_called_once()

    def test_start_recording_recorder_failure(self, manager, mock_components):
        """Test recording start with recorder failure"""
        mock_components['recorder'].start_recording.return_value = False
        
        success = manager.start_recording()
        
        assert not success
        assert not manager.is_recording
        assert manager.upload_thread is None
        mock_components['blockchain'].start_video_session.assert_called_once()

    def test_stop_recording(self, manager, mock_components):
        """Test recording stop"""
        # Start recording first
        manager.start_recording()
        assert manager.is_recording
        
        # Stop recording
        manager.stop_recording()
        
        assert not manager.is_recording
        assert manager.session_id is None
        mock_components['recorder'].stop_recording.assert_called_once()
        mock_components['processor'].stop.assert_called_once()
        mock_components['blockchain'].end_video_session.assert_called_once()

    def test_upload_loop_processing(self, manager, mock_components):
        """Test chunk upload processing"""
        # Configure mocks
        mock_chunk = create_mock_chunk()
        mock_components['recorder'].get_next_chunk.side_effect = [mock_chunk, None]
        mock_components['processor'].get_recent_results.return_value = [{
            'sequence_number': 0,
            'video_cid': 'mock_video_cid',
            'metadata_cid': 'mock_metadata_cid'
        }]
        
        # Start recording
        manager.start_recording()
        time.sleep(0.1)  # Let the upload loop run
        
        # Stop recording
        manager.stop_recording()
        
        # Verify chunk processing
        mock_components['processor'].add_chunk.assert_called_with(mock_chunk)
        mock_components['blockchain'].add_video_chunk.assert_called_once()

    def test_get_status(self, manager, mock_components):
        """Test status reporting"""
        status = manager.get_status()
        
        assert 'is_recording' in status
        assert 'session_id' in status
        assert 'recorder_status' in status
        assert 'processor_stats' in status
        assert 'session_active' in status
        
        mock_components['recorder'].get_status.assert_called_once()
        mock_components['processor'].get_stats.assert_called_once()

    def test_cleanup(self, manager, mock_components):
        """Test resource cleanup"""
        # Start recording
        manager.start_recording()
        assert manager.is_recording
        
        # Cleanup
        manager.cleanup()
        
        assert not manager.is_recording
        assert manager.session_id is None
        mock_components['recorder'].cleanup.assert_called_once()

    def test_error_handling(self, manager, mock_components):
        """Test error handling in various scenarios"""
        # Test blockchain error
        mock_components['blockchain'].start_video_session.side_effect = Exception("Blockchain error")
        success = manager.start_recording()
        assert not success
        assert not manager.is_recording
        
        # Reset mock
        mock_components['blockchain'].start_video_session.side_effect = None
        mock_components['blockchain'].start_video_session.return_value = 1
        
        # Test recorder error during upload
        manager.start_recording()
        mock_components['recorder'].get_next_chunk.side_effect = Exception("Recorder error")
        time.sleep(0.1)  # Let the upload loop run
        manager.stop_recording()
        
        # Verify error didn't crash the upload loop
        assert mock_components['processor'].stop.called

    @pytest.mark.parametrize("chunk_count", [1, 5, 10])
    def test_multiple_chunks(self, manager, mock_components, chunk_count):
        """Test processing multiple chunks"""
        # Configure mocks
        chunks = [create_mock_chunk(i) for i in range(chunk_count)]
        mock_components['recorder'].get_next_chunk.side_effect = chunks + [None]
        
        results = [{
            'sequence_number': i,
            'video_cid': f'video_cid_{i}',
            'metadata_cid': f'metadata_cid_{i}'
        } for i in range(chunk_count)]
        mock_components['processor'].get_recent_results.return_value = results
        
        # Start recording
        manager.start_recording()
        time.sleep(0.1 * chunk_count)  # Give time for processing
        manager.stop_recording()
        
        # Verify all chunks were processed
        assert mock_components['processor'].add_chunk.call_count == chunk_count
        assert mock_components['blockchain'].add_video_chunk.call_count == chunk_count
