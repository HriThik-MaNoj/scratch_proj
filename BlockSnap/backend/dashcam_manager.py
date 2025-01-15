#!/usr/bin/env python3

import logging
import threading
from typing import Optional, Dict
from datetime import datetime
import time
from .video_handler import DashcamRecorder
from .ipfs_handler import IPFSHandler
from .blockchain_handler import BlockchainHandler
from .batch_processor import BatchProcessor
from pathlib import Path

class DashcamManager:
    def __init__(self):
        """Initialize the dashcam manager"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.recorder = DashcamRecorder()
        self.ipfs = IPFSHandler()
        self.blockchain_handler = BlockchainHandler()
        self.batch_processor = BatchProcessor(self.ipfs)
        
        # Session state
        self.session_id: Optional[int] = None
        self.is_recording = False
        self.upload_thread: Optional[threading.Thread] = None
        self.current_session_chunks = []
        self.session_start_time = None
        self.session_metadata = {}
        self.current_chunk = 0
        
        # Error tracking
        self.last_error = None
        self.error_count = 0
        
        self.logger.info("DashcamManager initialized")

    def start_recording(self) -> bool:
        """Start recording and uploading"""
        try:
            # Reset state
            self.last_error = None
            self.error_count = 0
            
            # Start blockchain session
            self.session_id = self.blockchain_handler.start_video_session()
            self.session_start_time = datetime.now()
            
            # Initialize session metadata
            self.session_metadata = {
                'session_id': self.session_id,
                'start_time': self.session_start_time.isoformat(),
                'status': 'recording',
                'chunk_count': 0,
                'total_duration': 0,
                'creation_timestamp': int(time.time())
            }
            
            # Start video recording
            if not self.recorder.start_recording():
                raise RuntimeError("Failed to start recording")
            
            # Start batch processor
            self.batch_processor.start()
            
            # Start upload thread
            self.is_recording = True
            self.current_session_chunks = []
            self.current_chunk = 0
            self.upload_thread = threading.Thread(target=self._upload_loop)
            self.upload_thread.start()
            
            self.logger.info(f"Started recording with session ID: {self.session_id}")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Failed to start recording: {str(e)}")
            self.cleanup()
            return False

    def stop_recording(self) -> None:
        """Stop recording and finalize the session"""
        try:
            if not self.is_recording:
                self.logger.warning("No active recording session")
                return

            # Update session metadata
            self.session_metadata['status'] = 'completed'
            self.session_metadata['end_time'] = datetime.now().isoformat()
            self.session_metadata['total_duration'] = (
                datetime.now() - self.session_start_time
            ).total_seconds()
            
            # Stop recorder first
            self.recorder.stop_recording()
            
            # Signal upload thread to stop
            self.is_recording = False
            
            # Wait for upload thread with timeout
            if self.upload_thread and self.upload_thread.is_alive():
                self.upload_thread.join(timeout=10)  # Wait up to 10 seconds
            
            # Stop batch processor
            self.batch_processor.stop()
            
            # End blockchain session with final metadata
            if self.session_id is not None:
                try:
                    self.blockchain_handler.end_video_session(self.session_id)
                    self.logger.info(f"Ended session {self.session_id}")
                except Exception as e:
                    self.logger.error(f"Error ending blockchain session: {str(e)}")
                    raise

            self.logger.info("Stopped recording")
            
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Error stopping recording: {str(e)}")
        finally:
            # Ensure cleanup happens even if there's an error
            self.is_recording = False
            self.cleanup()

    def add_chunk(self, chunk) -> None:
        """Add a chunk to the batch processor"""
        try:
            self.batch_processor.add_chunk(chunk)
            self.current_chunk += 1
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.logger.error(f"Error adding chunk: {str(e)}")
            raise

    def _verify_chunk_upload(self, chunk_data):
        """Verify chunk was properly uploaded"""
        try:
            # Verify IPFS content exists
            if not self.ipfs.verify_content(chunk_data['video_cid']):
                raise ValueError(f"Video content missing: {chunk_data['video_cid']}")
            if not self.ipfs.verify_content(chunk_data['metadata_cid']):
                raise ValueError(f"Metadata missing: {chunk_data['metadata_cid']}")
            
            # Verify blockchain record
            if not self.blockchain_handler.verify_session_chunk(self.session_id, chunk_data):
                raise ValueError(f"Chunk not found in blockchain for session {self.session_id}")
            
            return True
        except Exception as e:
            self.logger.error(f"Chunk verification failed: {e}")
            return False

    def _upload_loop(self) -> None:
        """Main upload loop"""
        while self.is_recording:
            try:
                # Get processed results
                while not self.batch_processor.result_queue.empty():
                    result = self.batch_processor.result_queue.get()
                    self.logger.debug(f"Processing result: {result}")
                    
                    if result.get('success', False):
                        # Get the actual result data
                        chunk_data = result.get('result', {})
                        if not chunk_data:
                            chunk_data = result  # Handle case where result is not wrapped
                        
                        # Retry logic for blockchain upload
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                self.blockchain_handler.add_video_chunk(
                                    self.session_id,
                                    chunk_data
                                )
                                
                                # Verify upload
                                if self._verify_chunk_upload(chunk_data):
                                    self.logger.info(f"Successfully added and verified chunk {chunk_data.get('sequence_number')} to blockchain")
                                    break
                                else:
                                    raise ValueError("Chunk verification failed")
                                    
                            except Exception as e:
                                self.logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                                if attempt == max_retries - 1:
                                    self.error_count += 1
                                    self.last_error = f"Failed to add chunk to blockchain after {max_retries} attempts: {str(e)}"
                                    self.logger.error(self.last_error)
                                else:
                                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                    else:
                        self.error_count += 1
                        self.last_error = result.get('error', 'Unknown error in batch processing')
                        self.logger.error(f"Error processing chunk: {self.last_error}")
                
                time.sleep(0.1)  # Prevent busy waiting
                
            except Exception as e:
                self.error_count += 1
                self.last_error = str(e)
                self.logger.error(f"Error in upload loop: {str(e)}")

    def recover_session(self, session_id: int) -> bool:
        """
        Recover a failed session by reprocessing missing chunks
        Returns True if recovery was successful
        """
        try:
            # Get session metadata
            metadata = self.blockchain_handler.get_session_metadata(session_id)
            if not metadata:
                raise ValueError(f"No metadata found for session {session_id}")
            
            # Get existing chunks
            existing_chunks = self.blockchain_handler.get_session_chunks(session_id)
            saved_chunks = {c['sequence_number'] for c in existing_chunks}
            
            # Calculate missing chunks
            expected_chunks = set(range(metadata.get('chunk_count', 0)))
            missing_chunks = expected_chunks - saved_chunks
            
            if not missing_chunks:
                self.logger.info(f"No missing chunks found for session {session_id}")
                return True
            
            self.logger.info(f"Found {len(missing_chunks)} missing chunks for session {session_id}")
            
            # Reprocess missing chunks
            success = True
            for chunk_num in missing_chunks:
                chunk_path = self.recorder.temp_dir / f"chunk_{chunk_num}.mp4"
                if chunk_path.exists():
                    try:
                        with open(chunk_path, 'rb') as f:
                            chunk_data = f.read()
                        
                        chunk = VideoChunk(
                            start_time=metadata['start_time'] + (chunk_num * self.recorder.chunk_duration),
                            data=chunk_data,
                            sequence_number=chunk_num,
                            metadata={
                                'session_id': session_id,
                                'recovery': True
                            }
                        )
                        
                        self.add_chunk(chunk)
                        self.logger.info(f"Reprocessed chunk {chunk_num}")
                    except Exception as e:
                        self.logger.error(f"Failed to reprocess chunk {chunk_num}: {e}")
                        success = False
                else:
                    self.logger.warning(f"Missing chunk file for chunk {chunk_num}")
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to recover session {session_id}: {e}")
            return False

    def get_status(self) -> Dict:
        """Get current status with enhanced error reporting"""
        try:
            recorder_status = self.recorder.get_status()
            processor_stats = self.batch_processor.get_stats()
            
            # Get session status if active
            session_status = None
            if self.session_id is not None:
                try:
                    session_status = self.blockchain_handler.get_session_status(self.session_id)
                except Exception as e:
                    self.logger.error(f"Failed to get session status: {e}")
            
            return {
                'is_recording': self.is_recording,
                'session_id': self.session_id,
                'session_metadata': self.session_metadata,
                'session_status': session_status,
                'recorder_status': recorder_status,
                'processor_stats': processor_stats,
                'error_count': self.error_count,
                'last_error': self.last_error,
                'current_chunk': self.current_chunk,
                'temp_dir_size': sum(f.stat().st_size for f in Path(self.recorder.temp_dir).glob('*') if f.is_file()),
                'session_active': self.session_id is not None and 
                                self.blockchain_handler.is_session_active(self.session_id)
            }
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {'error': str(e)}

    def cleanup(self) -> None:
        """Clean up resources"""
        self.recorder.cleanup()
        self.is_recording = False
        self.session_id = None
        self.session_metadata = {}
