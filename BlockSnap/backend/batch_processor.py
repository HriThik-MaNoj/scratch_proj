#!/usr/bin/env python3

import logging
import threading
import queue
import time
from typing import List, Dict, Optional
from .ipfs_handler import IPFSHandler
import json

class BatchProcessor:
    def __init__(self, ipfs_handler: IPFSHandler, max_batch_size: int = 5):
        """Initialize the batch processor"""
        self.logger = logging.getLogger(__name__)
        self.ipfs = ipfs_handler
        self.max_batch_size = max_batch_size
        
        # Processing queues
        self.input_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # State
        self.is_running = False
        self.process_thread: Optional[threading.Thread] = None
        self.processed_count = 0
        self.failed_count = 0
        self.current_batch: List = []
        
        # Performance tracking
        self.last_process_time = 0
        self.avg_process_time = 0
        self.total_process_time = 0
        
    def start(self):
        """Start the processor"""
        if self.is_running:
            return
            
        self.is_running = True
        self.process_thread = threading.Thread(target=self._process_loop)
        self.process_thread.start()
        self.logger.info("Batch processor started")
        
    def stop(self):
        """Stop the processor"""
        self.is_running = False
        if self.process_thread:
            self.process_thread.join()
        self._process_remaining()
        self.logger.info("Batch processor stopped")
        
    def add_chunk(self, chunk) -> None:
        """Add a chunk to be processed"""
        if not self.is_running:
            self.logger.warning("Batch processor is not running")
            return
            
        self.input_queue.put(chunk)
        
    def get_latest_results(self) -> List[Dict]:
        """Get all available results"""
        results = []
        while not self.result_queue.empty():
            results.append(self.result_queue.get())
        return results
        
    def get_stats(self) -> Dict:
        """Get enhanced processor statistics"""
        stats = {
            'processed_count': self.processed_count,
            'failed_count': self.failed_count,
            'queue_size': self.input_queue.qsize(),
            'result_queue_size': self.result_queue.qsize(),
            'current_batch_size': len(self.current_batch),
            'success_rate': (
                (self.processed_count - self.failed_count) / self.processed_count * 100
                if self.processed_count > 0 else 0
            ),
            'average_process_time': (
                self.total_process_time / self.processed_count
                if self.processed_count > 0 else 0
            ),
            'is_running': self.is_running,
            'avg_process_time': self.avg_process_time,
            'last_process_time': self.last_process_time
        }
        return stats
        
    def _process_loop(self) -> None:
        """Main processing loop"""
        while self.is_running:
            try:
                # Build batch
                while len(self.current_batch) < self.max_batch_size:
                    try:
                        chunk = self.input_queue.get(timeout=1)
                        self.current_batch.append(chunk)
                    except queue.Empty:
                        break
                        
                if not self.current_batch:
                    time.sleep(0.1)
                    continue
                    
                # Process batch
                start_time = time.time()
                self._process_batch()
                process_time = time.time() - start_time
                
                # Update statistics
                self.last_process_time = process_time
                self.total_process_time += process_time
                self.avg_process_time = self.total_process_time / self.processed_count
                
                # Clear batch
                self.current_batch = []
                
            except Exception as e:
                self.logger.error(f"Error in process loop: {str(e)}")
                self.failed_count += 1
                time.sleep(1)
                
    def _process_batch(self) -> None:
        """Process a batch of chunks"""
        for chunk in self.current_batch:
            try:
                result = self.process_chunk(chunk)
                self.result_queue.put(result)
                self.processed_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to process chunk {chunk.sequence_number}: {str(e)}")
                self.failed_count += 1
                self.result_queue.put({
                    'success': False,
                    'error': str(e),
                    'sequence_number': chunk.sequence_number
                })
                
    def process_chunk(self, chunk) -> Dict:
        """Process a single chunk"""
        try:
            start_time = time.time()
            
            # Upload video data to IPFS with retry
            video_cid = None
            for attempt in range(3):
                try:
                    video_cid = self.ipfs.add_bytes(
                        chunk.data,
                        f"chunk_{chunk.sequence_number}.webm"
                    )
                    if video_cid:
                        break
                except Exception as e:
                    if attempt == 2:
                        raise
                    time.sleep(1)
            
            if not video_cid:
                raise ValueError("Failed to upload video to IPFS")
            
            # Create and upload metadata
            metadata = chunk.get_metadata()
            metadata['video_cid'] = video_cid
            metadata['process_time'] = time.time() - start_time
            
            metadata_json = json.dumps(metadata)
            metadata_cid = None
            
            # Upload metadata with retry
            for attempt in range(3):
                try:
                    metadata_cid = self.ipfs.add_bytes(
                        metadata_json.encode(),
                        f"chunk_{chunk.sequence_number}_metadata.json"
                    )
                    if metadata_cid:
                        break
                except Exception as e:
                    if attempt == 2:
                        raise
                    time.sleep(1)
            
            if not metadata_cid:
                raise ValueError("Failed to upload metadata to IPFS")
            
            # Verify IPFS content is accessible
            if not self.ipfs.verify_content(video_cid):
                raise ValueError(f"Video content verification failed: {video_cid}")
            if not self.ipfs.verify_content(metadata_cid):
                raise ValueError(f"Metadata verification failed: {metadata_cid}")
            
            result = {
                'video_cid': video_cid,
                'metadata_cid': metadata_cid,
                'sequence_number': chunk.sequence_number,
                'success': True,
                'process_time': time.time() - start_time
            }
            
            self.logger.info(f"Processed chunk {chunk.sequence_number}: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process chunk {chunk.sequence_number}: {str(e)}")
            raise
            
    def _process_remaining(self) -> None:
        """Process any remaining chunks in the queue"""
        while not self.input_queue.empty():
            try:
                chunk = self.input_queue.get_nowait()
                self.current_batch.append(chunk)
            except queue.Empty:
                break
                
        if self.current_batch:
            self._process_batch()
