#!/usr/bin/env python3

from web3 import Web3
from eth_account import Account
import json
import os
import logging
from typing import Tuple, Optional, Dict, List
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
import time

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
        
        # Initialize session cache
        self._sessions_cache = {}
        self._last_cache_update = 0
        self._cache_ttl = 300  # 5 minutes

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

    def add_video_chunk(self, session_id: int, chunk_data: Dict) -> None:
        """Add a video chunk to a session"""
        try:
            # Add chunk to contract
            tx = self.contract.functions.addVideoChunk(
                session_id,
                chunk_data['sequence_number'],
                chunk_data['video_cid'],
                chunk_data['metadata_cid']
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt with more confirmations
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt['status'] == 1:
                # Wait for a few more blocks to ensure indexing
                current_block = self.w3.eth.block_number
                while self.w3.eth.block_number < current_block + 1:
                    time.sleep(0.1)
                    
                self.logger.info(f"Added chunk {chunk_data['sequence_number']} to session {session_id}")
                
                # Clear session cache to force refresh
                if str(session_id) in self._sessions_cache:
                    del self._sessions_cache[str(session_id)]
            else:
                raise Exception("Transaction failed")
                
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

    def update_sessions_cache(self) -> None:
        """Update the sessions cache from blockchain"""
        try:
            sessions = {}
            # Get recent events only - last 1000 blocks
            current_block = self.w3.eth.block_number
            from_block = max(0, current_block - 1000)
            
            event_filter = self.contract.events.VideoSessionStarted.create_filter(
                fromBlock=from_block,
                toBlock='latest'
            )
            events = event_filter.get_all_entries()
            
            for event in events:
                session_id = event.args.sessionId
                owner = event.args.owner
                
                # Get chunks directly from contract call
                chunk_count = self.contract.functions.getSessionChunkCount(session_id).call()
                is_active = self.contract.functions.isSessionActive(session_id).call()
                
                sessions[session_id] = {
                    'session_id': session_id,
                    'owner': owner,
                    'chunk_count': chunk_count,
                    'is_active': is_active
                }
            
            self._sessions_cache = sessions
            self._last_cache_update = time.time()
            self.logger.info(f"Updated sessions cache with {len(sessions)} sessions")
            
        except Exception as e:
            self.logger.error(f"Failed to update sessions cache: {str(e)}")
            raise

    def get_session_chunks(self, session_id: int) -> list:
        """Get chunks for a specific session"""
        try:
            # Get chunk events for specific session
            chunk_filter = self.contract.events.VideoChunkAdded.create_filter(
                fromBlock=max(0, self.w3.eth.block_number - 1000),
                argument_filters={'sessionId': session_id}
            )
            events = chunk_filter.get_all_entries()
            
            chunks = []
            for event in events:
                chunks.append({
                    'sequence_number': event.args.sequenceNumber,
                    'video_cid': event.args.videoCID,
                    'timestamp': event.args.get('timestamp', int(time.time()))
                })
            
            return sorted(chunks, key=lambda x: x['sequence_number'])
            
        except Exception as e:
            self.logger.error(f"Failed to get session chunks: {str(e)}")
            return []

    def is_session_active(self, session_id: int) -> bool:
        """Check if a session is active"""
        try:
            return self.contract.functions.isSessionActive(session_id).call()
        except Exception as e:
            self.logger.error(f"Error checking session status: {str(e)}")
            raise

    def get_video_sessions(self, wallet_address):
        """Get all video sessions for a wallet address"""
        try:
            # Get event signatures
            start_event_sig = self.w3.keccak(text="VideoSessionStarted(uint256,address)").hex()
            chunk_event_sig = self.w3.keccak(text="VideoChunkAdded(uint256,uint256,string)").hex()
            end_event_sig = self.w3.keccak(text="VideoSessionEnded(uint256,uint256)").hex()
            
            # Format wallet address for topic filtering
            wallet_topic = '0x' + wallet_address[2:].lower().zfill(64)
            
            # Get all relevant events in a single query
            from_block = max(0, self.w3.eth.block_number - 1000)
            events = self.w3.eth.get_logs({
                'address': self.contract.address,
                'topics': [[start_event_sig, chunk_event_sig, end_event_sig]],
                'fromBlock': from_block,
                'toBlock': 'latest'
            })
            
            # Process events into sessions
            sessions = {}
            for event in events:
                try:
                    event_sig = event['topics'][0].hex()
                    
                    if event_sig == start_event_sig:
                        # New session
                        decoded = self.contract.events.VideoSessionStarted().process_log(event)
                        session_id = decoded['args']['sessionId']
                        owner = decoded['args']['owner']
                        
                        if owner.lower() == wallet_address.lower():
                            sessions[session_id] = {
                                'session_id': session_id,
                                'owner': owner,
                                'chunks': [],
                                'start_block': event['blockNumber'],
                                'transaction_hash': event['transactionHash'].hex(),
                                'is_active': True
                            }
                    
                    elif event_sig == chunk_event_sig and sessions:
                        # Add chunk to existing session
                        decoded = self.contract.events.VideoChunkAdded().process_log(event)
                        session_id = decoded['args']['sessionId']
                        
                        if session_id in sessions:
                            new_chunk = {
                                'sequence_number': decoded['args']['sequenceNumber'],
                                'video_cid': decoded['args']['videoCID'],
                                'timestamp': event['blockNumber'],
                                'transaction_hash': event['transactionHash'].hex()
                            }
                            
                            # Check if this chunk already exists
                            chunk_exists = False
                            for existing_chunk in sessions[session_id]['chunks']:
                                if (existing_chunk['sequence_number'] == new_chunk['sequence_number'] and 
                                    existing_chunk['video_cid'] == new_chunk['video_cid']):
                                    chunk_exists = True
                                    break
                            
                            if not chunk_exists:
                                sessions[session_id]['chunks'].append(new_chunk)
                    
                    elif event_sig == end_event_sig and sessions:
                        # Mark session as ended
                        decoded = self.contract.events.VideoSessionEnded().process_log(event)
                        session_id = decoded['args']['sessionId']
                        
                        if session_id in sessions:
                            sessions[session_id]['is_active'] = False
                            sessions[session_id]['end_block'] = event['blockNumber']
                    
                except Exception as e:
                    self.logger.warning(f"Error processing event: {str(e)}")
                    continue
            
            # Sort chunks and prepare final list
            result = []
            for session in sessions.values():
                session['chunks'].sort(key=lambda x: x['sequence_number'])
                result.append(session)
            
            # Sort sessions by start block
            result.sort(key=lambda x: x['start_block'], reverse=True)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get video sessions: {str(e)}")
            raise

    def verify_session_chunk(self, session_id, chunk_data):
        """Verify a chunk was properly added to a session"""
        try:
            session_chunks = self.get_session_chunks(session_id)
            return any(
                chunk['video_cid'] == chunk_data['video_cid']
                for chunk in session_chunks
            )
        except Exception as e:
            self.logger.error(f"Failed to verify chunk: {e}")
            return False

if __name__ == "__main__":
    # Example usage
    handler = BlockchainHandler()
    
    # Test verification
    test_cid = "QmTest123"
    exists, owner = handler.verify_photo(test_cid)
    print(f"Photo exists: {exists}")
    if exists:
        print(f"Owner: {owner}") 