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

class DashcamManager:
    def __init__(self):
        """Initialize the dashcam manager"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.recorder = DashcamRecorder()
        self.ipfs = IPFSHandler()
        self.blockchain = BlockchainHandler()
        self.batch_processor = BatchProcessor(self.ipfs)
        
        # State
        self.session_id: Optional[int] = None
        self.is_recording = False
        self.upload_thread: Optional[threading.Thread] = None
        self.current_session_chunks = []
        self.session_start_time = None
        
        self.logger.info("DashcamManager initialized")

    def start_recording(self) -> bool:
        """Start recording and uploading"""
        try:
            # Start blockchain session
            self.session_id = self.blockchain.start_video_session()
            self.session_start_time = datetime.now()
            
            # Start video recording
            if not self.recorder.start_recording():
                raise RuntimeError("Failed to start recording")
            
            # Start batch processor
            self.batch_processor.start()
            
            # Start upload thread
            self.is_recording = True
            self.current_session_chunks = []
            self.upload_thread = threading.Thread(target=self._upload_loop)
            self.upload_thread.start()
            
            self.logger.info(f"Started recording with session ID: {self.session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {str(e)}")
            self.cleanup()
            return False

    def stop_recording(self) -> None:
        """Stop recording and uploading"""
        try:
            self.is_recording = False
            
            # Stop recorder
            self.recorder.stop_recording()
            
            # Wait for upload thread
            if self.upload_thread:
                self.upload_thread.join()
            
            # Stop batch processor
            self.batch_processor.stop()
            
            # End blockchain session
            if self.session_id is not None:
                self.blockchain.end_video_session(self.session_id)
            
            self.logger.info("Stopped recording")
            
        except Exception as e:
            self.logger.error(f"Error stopping recording: {str(e)}")
        finally:
            self.cleanup()

    def _upload_loop(self) -> None:
        """Main upload loop"""
        while self.is_recording:
            try:
                chunk = self.recorder.get_next_chunk()
                if chunk:
                    # Add session metadata
                    chunk.metadata.update({
                        'session_id': self.session_id,
                        'session_start_time': self.session_start_time.isoformat(),
                        'chunk_number': len(self.current_session_chunks) + 1
                    })
                    
                    # Add to batch processor
                    self.batch_processor.add_chunk(chunk)
                    self.current_session_chunks.append(chunk)
                    
                    # Process results
                    results = self.batch_processor.get_latest_results()
                    for result in results:
                        if result.get('success'):
                            self.blockchain.add_video_chunk(
                                self.session_id,
                                {
                                    'video_cid': result['video_cid'],
                                    'metadata_cid': result['metadata_cid'],
                                    'sequence_number': result['sequence_number']
                                }
                            )
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                self.logger.error(f"Error in upload loop: {str(e)}")
                continue

    def get_status(self) -> Dict:
        """Get current status"""
        try:
            return {
                'is_recording': self.is_recording,
                'session_id': self.session_id,
                'recorder_status': self.recorder.get_status(),
                'processor_stats': self.batch_processor.get_stats(),
                'session_active': self.session_id is not None and 
                                self.blockchain.is_session_active(self.session_id)
            }
        except Exception as e:
            self.logger.error(f"Error getting status: {str(e)}")
            return {'error': str(e)}

    def cleanup(self) -> None:
        """Clean up resources"""
        self.recorder.cleanup()
        self.is_recording = False
        self.session_id = None
