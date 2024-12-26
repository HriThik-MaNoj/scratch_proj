#!/usr/bin/env python3

import os
import time
from datetime import datetime
import json
import RPi.GPIO as GPIO
from picamera2 import Picamera2
import logging
from pathlib import Path

class BlockSnapCamera:
    def __init__(self, 
                 shutter_pin=17,  # GPIO pin for shutter button
                 led_pin=27,      # GPIO pin for status LED
                 image_dir='captures'):
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(shutter_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(led_pin, GPIO.OUT)
        self.shutter_pin = shutter_pin
        self.led_pin = led_pin
        
        # Initialize camera
        self.camera = Picamera2()
        self.camera.configure(self.camera.create_still_configuration())
        self.camera.start()
        
        # Ensure image directory exists
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("BlockSnap Camera initialized successfully")
    
    def capture_image(self):
        """Capture an image and return the file path and metadata"""
        try:
            # Flash LED to indicate capture
            GPIO.output(self.led_pin, GPIO.HIGH)
            
            # Generate timestamp and filename
            timestamp = datetime.now().isoformat()
            filename = f"blocksnap_{timestamp.replace(':', '-')}.jpg"
            filepath = self.image_dir / filename
            
            # Capture image
            self.camera.capture_file(str(filepath))
            
            # Generate metadata
            metadata = {
                "timestamp": timestamp,
                "device": "Raspberry Pi Camera",
                "filename": filename,
                "filepath": str(filepath),
                "device_id": os.uname().nodename,
                # Add GPS coordinates if available
                # "gps": {"latitude": lat, "longitude": lon}
            }
            
            self.logger.info(f"Image captured: {filepath}")
            GPIO.output(self.led_pin, GPIO.LOW)
            
            return str(filepath), metadata
            
        except Exception as e:
            self.logger.error(f"Error capturing image: {str(e)}")
            GPIO.output(self.led_pin, GPIO.LOW)
            raise
    
    def start_capture_loop(self):
        """Start the main capture loop, waiting for button press"""
        self.logger.info("Starting capture loop. Press the shutter button to capture.")
        
        try:
            while True:
                # Wait for button press (falling edge)
                if GPIO.wait_for_edge(self.shutter_pin, GPIO.FALLING, timeout=1000):
                    filepath, metadata = self.capture_image()
                    
                    # Save metadata alongside image
                    metadata_path = Path(filepath).with_suffix('.json')
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    time.sleep(0.5)  # Debounce
                
        except KeyboardInterrupt:
            self.logger.info("Capture loop stopped by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up GPIO and camera resources"""
        GPIO.cleanup()
        self.camera.stop()
        self.logger.info("Camera resources cleaned up")

if __name__ == "__main__":
    camera = BlockSnapCamera()
    camera.start_capture_loop() 