#!/usr/bin/env python3

from web3 import Web3
from eth_account import Account
import json
import os
import logging
from typing import Tuple, Optional, Dict, List
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class BlockchainHandler:
    def __init__(self):
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        self.rpc_url = os.getenv('ETH_RPC_URL', 'https://rpc.buildbear.io/impossible-omegared-15eaf7dd')
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        self.private_key = os.getenv('PRIVATE_KEY')
        
        if not all([self.rpc_url, self.contract_address, self.private_key]):
            raise ValueError("Missing required environment variables")
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum network")
        
        # Load contract ABI
        contract_path = Path(__file__).parent.parent / 'artifacts' / 'smart_contracts' / 'BlockSnapNFT.sol' / 'BlockSnapNFT.json'
        if not contract_path.exists():
            raise FileNotFoundError(f"Contract ABI file not found at {contract_path}")
            
        with open(contract_path) as f:
            contract_json = json.load(f)
            self.contract_abi = contract_json['abi']
            self.logger.info("Successfully loaded contract ABI")
        
        # Initialize contract
        self.contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.contract_address),
            abi=self.contract_abi
        )
        
        # Initialize account
        self.account = Account.from_key(self.private_key)
        self.logger.info(f"Initialized with account: {self.account.address}")
    
    def mint_photo_nft(self, 
                      to_address: str, 
                      image_cid: str, 
                      metadata_uri: str) -> Tuple[str, int]:
        """
        Mint a new photo NFT
        Returns: Tuple(transaction_hash, token_id)
        """
        try:
            # Prepare transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Build transaction
            tx = self.contract.functions.mintPhoto(
                self.w3.to_checksum_address(to_address),
                image_cid,
                metadata_uri
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Get token ID from event logs
            mint_event = self.contract.events.PhotoMinted().process_receipt(receipt)[0]
            token_id = mint_event['args']['tokenId']
            
            self.logger.info(f"Successfully minted NFT with token ID: {token_id}")
            return (self.w3.to_hex(tx_hash), token_id)
            
        except Exception as e:
            self.logger.error(f"Error minting NFT: {str(e)}")
            raise
    
    def verify_photo(self, image_cid: str) -> Tuple[bool, Optional[str]]:
        """
        Verify if a photo exists and get its owner
        Returns: Tuple(exists, owner_address)
        """
        try:
            exists, owner = self.contract.functions.verifyPhoto(image_cid).call()
            return exists, owner if exists else None
        except Exception as e:
            self.logger.error(f"Error verifying photo: {str(e)}")
            raise
    
    def get_token_uri(self, token_id: int) -> str:
        """Get the metadata URI for a token"""
        try:
            return self.contract.functions.tokenURI(token_id).call()
        except Exception as e:
            self.logger.error(f"Error getting token URI: {str(e)}")
            raise
    
    def get_image_cid(self, token_id: int) -> str:
        """Get the image CID for a token"""
        try:
            return self.contract.functions.getImageCID(token_id).call()
        except Exception as e:
            self.logger.error(f"Error getting image CID: {str(e)}")
            raise

    def start_video_session(self) -> int:
        """Start a new video recording session"""
        try:
            # Prepare transaction
            tx = self.contract.functions.startVideoSession().build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Get session ID from event
            session_event = self.contract.events.VideoSessionStarted().process_receipt(receipt)[0]
            session_id = session_event['args']['sessionId']
            
            self.logger.info(f"Started video session with ID: {session_id}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Error starting video session: {str(e)}")
            raise

    def add_video_chunk(self, session_id: int, chunk_data: Dict[str, str]) -> str:
        """
        Add a video chunk to an active session
        Args:
            session_id: Active session ID
            chunk_data: Dict containing video_cid, metadata_cid, and sequence_number
        Returns:
            Transaction hash
        """
        try:
            # Prepare transaction
            tx = self.contract.functions.addVideoChunk(
                session_id,
                chunk_data['sequence_number'],
                chunk_data['video_cid'],
                chunk_data['metadata_cid']
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            self.logger.info(f"Added chunk {chunk_data['sequence_number']} to session {session_id}")
            return self.w3.to_hex(tx_hash)
            
        except Exception as e:
            self.logger.error(f"Error adding video chunk: {str(e)}")
            raise

    def end_video_session(self, session_id: int) -> str:
        """End a video recording session"""
        try:
            # Prepare transaction
            tx = self.contract.functions.endVideoSession(session_id).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            self.logger.info(f"Ended video session {session_id}")
            return self.w3.to_hex(tx_hash)
            
        except Exception as e:
            self.logger.error(f"Error ending video session: {str(e)}")
            raise

    def get_session_chunks(self, session_id: int) -> List[Dict[str, str]]:
        """Get all chunks for a video session"""
        try:
            chunks = self.contract.functions.getSessionChunks(session_id).call()
            return [{
                'session_id': chunk[0],
                'sequence_number': chunk[1],
                'video_cid': chunk[2],
                'metadata_cid': chunk[3],
                'timestamp': chunk[4]
            } for chunk in chunks]
        except Exception as e:
            self.logger.error(f"Error getting session chunks: {str(e)}")
            raise

    def is_session_active(self, session_id: int) -> bool:
        """Check if a session is active"""
        try:
            return self.contract.functions.isSessionActive(session_id).call()
        except Exception as e:
            self.logger.error(f"Error checking session status: {str(e)}")
            raise

if __name__ == "__main__":
    # Example usage
    handler = BlockchainHandler()
    
    # Test verification
    test_cid = "QmTest123"
    exists, owner = handler.verify_photo(test_cid)
    print(f"Photo exists: {exists}")
    if exists:
        print(f"Owner: {owner}") 