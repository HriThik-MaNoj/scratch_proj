#!/usr/bin/env python3

import threading
import queue
import logging
import time
from typing import Optional, List, Dict
from collections import deque

class BatchProcessor:
    def __init__(self, ipfs_handler, batch_size: int = 5, max_queue_size: int = 100):
        """
        Initialize batch processor for video chunks
        Args:
            ipfs_handler: IPFSHandler instance
            batch_size: Number of chunks to process in parallel
            max_queue_size: Maximum number of chunks to keep in queue
        """
        self.logger = logging.getLogger(__name__)
        self.ipfs_handler = ipfs_handler
        self.batch_size = batch_size
        self.processing_queue = queue.Queue(maxsize=max_queue_size)
        self.results = deque(maxlen=1000)  # Keep last 1000 results
        
        self.is_processing = False
        self.processor_thread: Optional[threading.Thread] = None
        self.upload_stats = {
            'total_processed': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'last_batch_time': 0
        }

    def start(self) -> None:
        """Start the batch processor"""
        if self.is_processing:
            return
            
        self.is_processing = True
        self.processor_thread = threading.Thread(target=self._process_loop)
        self.processor_thread.start()
        self.logger.info("Batch processor started")

    def stop(self) -> None:
        """Stop the batch processor"""
        self.is_processing = False
        if self.processor_thread:
            self.processor_thread.join()
        self.logger.info("Batch processor stopped")

    def add_chunk(self, chunk) -> None:
        """Add a chunk to the processing queue"""
        try:
            self.processing_queue.put(chunk, block=False)
        except queue.Full:
            self.logger.warning("Processing queue is full, dropping oldest chunk")
            _ = self.processing_queue.get()  # Remove oldest chunk
            self.processing_queue.put(chunk)  # Add new chunk

    def _process_loop(self) -> None:
        """Main processing loop"""
        while self.is_processing:
            try:
                chunks = []
                # Collect chunks for batch processing
                while len(chunks) < self.batch_size:
                    try:
                        chunk = self.processing_queue.get_nowait()
                        chunks.append(chunk)
                    except queue.Empty:
                        break

                if not chunks:
                    time.sleep(0.1)  # Prevent CPU spinning
                    continue

                # Process batch
                start_time = time.time()
                results = self.ipfs_handler.batch_upload_chunks(chunks)
                
                # Update stats
                self.upload_stats['total_processed'] += len(chunks)
                self.upload_stats['successful_uploads'] += len(results)
                self.upload_stats['failed_uploads'] += len(chunks) - len(results)
                self.upload_stats['last_batch_time'] = time.time() - start_time
                
                # Store results
                self.results.extend(results)

            except Exception as e:
                self.logger.error(f"Error in batch processing: {str(e)}")
                continue

    def get_stats(self) -> Dict:
        """Get current processing stats"""
        return {
            **self.upload_stats,
            'queue_size': self.processing_queue.qsize(),
            'is_processing': self.is_processing
        }

    def get_recent_results(self, limit: int = 10) -> List[Dict]:
        """Get most recent upload results"""
        return list(self.results)[-limit:]
