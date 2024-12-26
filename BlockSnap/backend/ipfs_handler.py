#!/usr/bin/env python3

import os
import logging
from dotenv import load_dotenv
from pathlib import Path
import requests
import json
from typing import Dict, Tuple, Optional

class IPFSHandler:
    def __init__(self):
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        load_dotenv()
        self.ipfs_host = os.getenv('IPFS_HOST', '/ip4/127.0.0.1/tcp/5001').replace('/ip4/127.0.0.1/tcp/', 'http://localhost:')
        self.ipfs_gateway = os.getenv('IPFS_GATEWAY', 'https://ipfs.io')
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
            if isinstance(file_path, str) and not os.path.isfile(file_path):
                # If it's a string but not a file path, treat it as content
                files = {
                    'file': ('content.txt', file_path.encode())
                }
            else:
                # It's a file path
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
            
            if isinstance(file_path, str) and os.path.isfile(file_path):
                files['file'][1].close()
            
            self.logger.info(f"Added file to IPFS with CID: {cid}")
            return cid
        except Exception as e:
            self.logger.error(f"Error adding file to IPFS: {str(e)}")
            raise

    def get_file(self, cid: str, output_path: str) -> bool:
        """Retrieve a file from IPFS by its CID"""
        try:
            # Create output directory if it doesn't exist
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Try local IPFS node first
            try:
                response = requests.post(
                    f"{self.ipfs_host}/api/v0/cat",
                    params={'arg': cid},
                    stream=True
                )
                response.raise_for_status()
            except Exception as local_error:
                # If local node fails, try IPFS gateway
                self.logger.warning(f"Failed to get file from local node: {str(local_error)}")
                response = requests.get(f"{self.ipfs_gateway}/ipfs/{cid}", stream=True)
                response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Retrieved file from IPFS: {cid}")
            return True
        except Exception as e:
            self.logger.error(f"Error retrieving file from IPFS: {str(e)}")
            raise

    def pin_file(self, cid: str) -> bool:
        """Pin a file to keep it in IPFS"""
        try:
            response = requests.post(
                f"{self.ipfs_host}/api/v0/pin/add",
                params={'arg': cid}
            )
            response.raise_for_status()
            
            self.logger.info(f"Pinned file in IPFS: {cid}")
            return True
        except Exception as e:
            self.logger.error(f"Error pinning file in IPFS: {str(e)}")
            raise

    def _pin_to_pinata(self, cid: str) -> None:
        """Pin a CID to Pinata"""
        if not (self.pinata_api_key and self.pinata_secret_key):
            self.logger.warning("Pinata credentials not configured")
            return
            
        try:
            headers = {
                'pinata_api_key': self.pinata_api_key,
                'pinata_secret_api_key': self.pinata_secret_key
            }
            
            json_data = {
                'hashToPin': cid,
                'pinataMetadata': {
                    'name': f'BlockSnap_{cid}'
                }
            }
            
            response = requests.post(
                'https://api.pinata.cloud/pinning/pinByHash',
                headers=headers,
                json=json_data
            )
            response.raise_for_status()
            
            self.logger.info(f"Successfully pinned {cid} to Pinata")
                
        except Exception as e:
            self.logger.error(f"Error pinning to Pinata: {str(e)}")

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

    def upload_to_ipfs(self, file_path: str, metadata: Dict) -> Tuple[str, str]:
        """
        Upload file and metadata to IPFS
        Returns: Tuple(file_cid, metadata_cid)
        """
        try:
            # Upload the file
            file_cid = self.add_file(file_path)
            self.logger.info(f"File uploaded to IPFS with CID: {file_cid}")
            
            # Add IPFS CID to metadata
            metadata['ipfs_cid'] = file_cid
            
            # Upload metadata
            metadata_cid = self.add_file(json.dumps(metadata))
            self.logger.info(f"Metadata uploaded to IPFS with CID: {metadata_cid}")
            
            # Pin to Pinata if configured
            if self.use_pinata:
                self._pin_to_pinata(file_cid)
                self._pin_to_pinata(metadata_cid)
            
            return file_cid, metadata_cid
            
        except Exception as e:
            self.logger.error(f"Error uploading to IPFS: {str(e)}")
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