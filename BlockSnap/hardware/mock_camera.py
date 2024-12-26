#!/usr/bin/env python3

import os
import time
from datetime import datetime
import json
import logging
from pathlib import Path
import cv2
import numpy as np

class MockCamera:
    def __init__(self, 
                 image_dir='captures',
                 test_image_size=(1920, 1080)):
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Store configuration
        self.image_size = test_image_size
        
        # Ensure image directory exists
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Mock Camera initialized successfully")
    
    def capture_image(self):
        """Generate a test image and return the file path and metadata"""
        try:
            # Generate timestamp and filename
            timestamp = datetime.now().isoformat()
            filename = f"blocksnap_{timestamp.replace(':', '-')}.jpg"
            filepath = self.image_dir / filename
            
            # Create a test image (gradient pattern)
            img = np.zeros((*self.image_size, 3), dtype=np.uint8)
            gradient = np.linspace(0, 255, self.image_size[1], dtype=np.uint8)
            img[:, :, 0] = gradient[np.newaxis, :]  # Red channel
            img[:, :, 1] = gradient[:, np.newaxis]  # Green channel
            img[:, :, 2] = 255 - gradient[np.newaxis, :]  # Blue channel
            
            # Add timestamp text to image
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(img, f'Test Image: {timestamp}', 
                       (50, 50), font, 1, (255, 255, 255), 2)
            
            # Save image
            cv2.imwrite(str(filepath), img)
            
            # Generate metadata
            metadata = {
                "timestamp": timestamp,
                "device": "Mock Camera",
                "filename": filename,
                "filepath": str(filepath),
                "device_id": "mock_device",
                "test_metadata": {
                    "image_size": self.image_size,
                    "is_mock": True
                }
            }
            
            self.logger.info(f"Mock image captured: {filepath}")
            return str(filepath), metadata
            
        except Exception as e:
            self.logger.error(f"Error capturing mock image: {str(e)}")
            raise
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Mock camera cleanup completed")

if __name__ == "__main__":
    # Test the mock camera
    camera = MockCamera()
    filepath, metadata = camera.capture_image()
    print(f"Test image saved to: {filepath}")
    print("Metadata:", json.dumps(metadata, indent=2)) 