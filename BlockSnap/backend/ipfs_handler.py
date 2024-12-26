#!/usr/bin/env python3

import os
import logging
import requests
import json
from typing import Dict, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv

class IPFSHandler:
    def __init__(self):
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        load_dotenv()
        self.ipfs_host = os.getenv('IPFS_HOST', 'http://127.0.0.1:5001')
        self.ipfs_gateway = os.getenv('IPFS_GATEWAY', 'http://127.0.0.1:8080')
        self.use_pinata = os.getenv('USE_PINATA', 'false').lower() == 'true'
        self.pinata_api_key = os.getenv('PINATA_API_KEY')
        self.pinata_secret_key = os.getenv('PINATA_SECRET_KEY')
        
        try:
            # Test connection to IPFS daemon
            response = requests.post(f"{self.ipfs_host}/api/v0/version")
            response.raise_for_status()
            self.logger.info(f"Connected to IPFS daemon at {self.ipfs_host}")
        except Exception as e:
            self.logger.error(f"Failed to connect to IPFS daemon: {str(e)}")
            raise

    def add_file(self, file_path: str) -> str:
        """Add a file to IPFS and return its CID"""
        try:
            if self.use_pinata:
                # Use Pinata for file upload
                if isinstance(file_path, str) and not os.path.isfile(file_path):
                    files = {
                        'file': ('content.txt', file_path.encode())
                    }
                else:
                    files = {
                        'file': ('file', open(file_path, 'rb'))
                    }

                headers = {
                    'pinata_api_key': self.pinata_api_key,
                    'pinata_secret_api_key': self.pinata_secret_key
                }

                response = requests.post(
                    'https://api.pinata.cloud/pinning/pinFileToIPFS',
                    files=files,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                cid = result['IpfsHash']
            else:
                # Use local IPFS node
                if isinstance(file_path, str) and not os.path.isfile(file_path):
                    files = {
                        'file': ('content.txt', file_path.encode())
                    }
                else:
                    files = {
                        'file': ('file', open(file_path, 'rb'))
                    }
                
                response = requests.post(
                    f"{self.ipfs_host}/api/v0/add",
                    files=files
                )
                response.raise_for_status()
                
                result = response.json()
                cid = result['Hash']
                
                # Pin the file locally
                self.pin_file(cid)
            
            if isinstance(file_path, str) and os.path.isfile(file_path):
                files['file'][1].close()
            
            self.logger.info(f"Added file to IPFS with CID: {cid}")
            return cid
        except Exception as e:
            self.logger.error(f"Error adding file to IPFS: {str(e)}")
            raise

    def pin_file(self, cid: str) -> None:
        """Pin a file on IPFS"""
        try:
            response = requests.post(
                f"{self.ipfs_host}/api/v0/pin/add",
                params={'arg': cid}
            )
            response.raise_for_status()
            self.logger.info(f"Successfully pinned CID: {cid}")
        except Exception as e:
            self.logger.error(f"Error pinning file: {str(e)}")
            raise

    def upload_to_ipfs(self, file_path: str, metadata: Dict) -> Tuple[str, str]:
        """
        Upload file and metadata to IPFS
        Returns: Tuple(file_cid, metadata_cid)
        """
        try:
            # Upload the file first
            file_cid = self.add_file(file_path)
            self.logger.info(f"File uploaded to IPFS with CID: {file_cid}")
            
            # Create metadata with proper NFT format
            full_metadata = {
                'name': f'BlockSnap #{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'description': 'A photo captured and authenticated using BlockSnap',
                'image': f'ipfs://{file_cid}',
                'image_url': self.get_ipfs_url(file_cid),
                'attributes': [
                    {
                        'trait_type': 'Platform',
                        'value': metadata.get('platform', 'Unknown')
                    },
                    {
                        'trait_type': 'Source',
                        'value': metadata.get('source', 'Unknown')
                    },
                    {
                        'trait_type': 'Timestamp',
                        'value': metadata.get('timestamp', datetime.now().isoformat())
                    }
                ]
            }
            
            # Upload metadata
            metadata_cid = self.add_file(json.dumps(full_metadata))
            self.logger.info(f"Metadata uploaded to IPFS with CID: {metadata_cid}")
            
            # Pin to Pinata if configured
            if self.use_pinata:
                self._pin_to_pinata(file_cid)
                self._pin_to_pinata(metadata_cid)
            
            return file_cid, metadata_cid
            
        except Exception as e:
            self.logger.error(f"Error uploading to IPFS: {str(e)}")
            raise

    def get_ipfs_url(self, cid: str) -> str:
        """Get a gateway URL for the IPFS content"""
        return f"{self.ipfs_gateway}/ipfs/{cid}"
    
    def verify_content(self, cid: str) -> bool:
        """Verify if content exists on IPFS"""
        try:
            response = requests.post(
                f"{self.ipfs_host}/api/v0/cat",
                params={'arg': cid}
            )
            response.raise_for_status()
            return True
        except Exception:
            return False

    def _pin_to_pinata(self, cid: str) -> None:
        """Pin a file to Pinata"""
        try:
            headers = {
                'pinata_api_key': self.pinata_api_key,
                'pinata_secret_api_key': self.pinata_secret_key
            }

            response = requests.post(
                'https://api.pinata.cloud/pinning/pinByHash',
                json={'hashToPin': cid},
                headers=headers
            )
            response.raise_for_status()
            self.logger.info(f"Successfully pinned CID to Pinata: {cid}")
        except Exception as e:
            self.logger.error(f"Error pinning to Pinata: {str(e)}")
            raise

if __name__ == "__main__":
    # Example usage
    handler = IPFSHandler()
    
    # Test file upload
    test_data = {"test": "data"}
    with open("test.json", "w") as f:
        json.dump(test_data, f)
    
    try:
        file_cid, metadata_cid = handler.upload_to_ipfs("test.json", test_data)
        print(f"File CID: {file_cid}")
        print(f"Metadata CID: {metadata_cid}")
    finally:
        os.remove("test.json")