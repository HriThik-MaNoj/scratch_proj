#!/usr/bin/env python3

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import cv2
import numpy as np
import os
import time
import logging
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
import platform
import json
import base64
import tempfile

# Import our custom modules
try:
    # Try to import Raspberry Pi specific modules
    from hardware.camera import BlockSnapCamera
    IS_RASPBERRY_PI = True
except (ImportError, RuntimeError):
    # If import fails, use mock camera
    from hardware.mock_camera import MockCamera
    IS_RASPBERRY_PI = False

from backend.ipfs_handler import IPFSHandler
from backend.blockchain_handler import BlockchainHandler
from backend.dashcam_manager import DashcamManager
from backend.video_handler import VideoChunk  # Import VideoChunk from video_handler instead

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
try:
    # Initialize camera based on platform
    if IS_RASPBERRY_PI:
        logger.info("Initializing Raspberry Pi camera")
        camera = BlockSnapCamera()
    else:
        logger.info("Initializing mock camera for testing")
        camera = MockCamera()
    
    ipfs_handler = IPFSHandler()
    blockchain_handler = BlockchainHandler()
    dashcam_manager = DashcamManager()  # Initialize dashcam manager
    logger.info("All components initialized successfully")
except Exception as e:
    logger.error(f"Error initializing components: {str(e)}")
    raise

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'platform': 'Raspberry Pi' if IS_RASPBERRY_PI else 'Test Environment'
    })

@app.route('/capture', methods=['POST'])
def capture_photo():
    """
    Capture a photo and store it on IPFS
    Required JSON body: {
        "wallet_address": "0x...",
        "image_data": "base64_encoded_image_data"
    }
    """
    try:
        # Validate request
        data = request.get_json()
        if not data or 'wallet_address' not in data or 'image_data' not in data:
            return jsonify({'error': 'wallet_address and image_data are required'}), 400
        
        wallet_address = data['wallet_address']
        image_data = data['image_data']
        
        # Save base64 image data to a temporary file
        import base64
        import tempfile
        
        # Remove the data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Decode base64 and save to temp file
        image_bytes = base64.b64decode(image_data)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(image_bytes)
            filepath = temp_file.name
        
        # Create metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform.system(),
            'source': 'web_capture'
        }
        
        # Upload to IPFS
        file_cid, metadata_cid = ipfs_handler.upload_to_ipfs(filepath, metadata)
        
        # Clean up temp file
        os.unlink(filepath)
        
        # Create metadata URI (IPFS gateway URL)
        metadata_uri = ipfs_handler.get_ipfs_url(metadata_cid)
        
        # Mint NFT
        tx_hash, token_id = blockchain_handler.mint_photo_nft(
            wallet_address,
            file_cid,
            metadata_uri
        )
        
        # Prepare response
        response = {
            'status': 'success',
            'data': {
                'file_cid': file_cid,
                'metadata_cid': metadata_cid,
                'token_id': token_id,
                'transaction_hash': tx_hash,
                'metadata_uri': metadata_uri,
                'image_url': ipfs_handler.get_ipfs_url(file_cid)
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in capture endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/verify/<image_cid>', methods=['GET'])
def verify_photo(image_cid):
    """Verify a photo's authenticity and ownership"""
    try:
        # Check if content exists on IPFS
        ipfs_exists = ipfs_handler.verify_content(image_cid)
        
        # Check blockchain records
        blockchain_exists, owner = blockchain_handler.verify_photo(image_cid)
        
        response = {
            'exists_on_ipfs': ipfs_exists,
            'exists_on_blockchain': blockchain_exists,
            'owner': owner if blockchain_exists else None,
            'ipfs_url': ipfs_handler.get_ipfs_url(image_cid) if ipfs_exists else None
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in verify endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/token/<int:token_id>', methods=['GET'])
def get_token_info(token_id):
    """Get information about a specific token"""
    try:
        metadata_uri = blockchain_handler.get_token_uri(token_id)
        image_cid = blockchain_handler.get_image_cid(token_id)
        
        response = {
            'token_id': token_id,
            'metadata_uri': metadata_uri,
            'image_cid': image_cid,
            'image_url': ipfs_handler.get_ipfs_url(image_cid)
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in token info endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/nfts/<wallet_address>', methods=['GET'])
def get_nfts_by_wallet(wallet_address):
    """Get all NFTs owned by a wallet address"""
    try:
        # Get the event signature for PhotoMinted
        event_signature_hash = blockchain_handler.w3.keccak(text="PhotoMinted(uint256,address,string,string)").hex()
        
        # Get logs for the PhotoMinted event
        logs = blockchain_handler.w3.eth.get_logs({
            'address': blockchain_handler.contract.address,
            'topics': [event_signature_hash],
            'fromBlock': 0,
            'toBlock': 'latest'
        })
        
        app.logger.info(f"Found {len(logs)} total PhotoMinted events")
        
        nfts = []
        # Check each token from logs
        for log in logs:
            try:
                # Decode the log data
                decoded_log = blockchain_handler.contract.events.PhotoMinted().process_log(log)
                token_id = decoded_log['args']['tokenId']
                
                # Check if this wallet owns the token
                owner = blockchain_handler.contract.functions.ownerOf(token_id).call()
                if owner.lower() == wallet_address.lower():
                    # Get token details
                    metadata_uri = blockchain_handler.get_token_uri(token_id)
                    image_cid = blockchain_handler.get_image_cid(token_id)
                    
                    # Get transaction hash from the event log
                    transaction_hash = decoded_log.transactionHash.hex()
                    
                    # Get metadata from IPFS if available
                    metadata = ipfs_handler.get_json(metadata_uri) or {
                        'name': f'BlockSnap #{token_id}',
                        'description': 'A photo captured using BlockSnap'
                    }
                    
                    nft = {
                        'tokenId': token_id,
                        'name': metadata.get('name', f'BlockSnap #{token_id}'),
                        'description': metadata.get('description', 'A photo captured using BlockSnap'),
                        'image': ipfs_handler.get_ipfs_url(image_cid),
                        'image_cid': image_cid,
                        'metadata_uri': metadata_uri,
                        'transaction_hash': transaction_hash
                    }
                    nfts.append(nft)
                    app.logger.info(f"Found NFT {token_id} owned by {wallet_address}")
            except Exception as e:
                app.logger.error(f"Error processing log: {str(e)}")
                continue
        
        return jsonify({'nfts': nfts})
        
    except Exception as e:
        app.logger.error(f"Error in get NFTs endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/video-sessions/<wallet_address>', methods=['GET'])
def get_video_sessions(wallet_address):
    """Get all video sessions for a wallet"""
    try:
        sessions = blockchain_handler.get_video_sessions(wallet_address)
        
        # Enhance session data with IPFS content
        for session in sessions:
            session_id = session.get('session_id')
            try:
                chunks = []
                for chunk in session.get('chunks', []):
                    try:
                        # Check if video is available in IPFS
                        is_available = ipfs_handler.verify_content(chunk['video_cid'])
                        chunk_data = {
                            'video_cid': chunk['video_cid'],
                            'sequence_number': chunk['sequence_number'],
                            'timestamp': chunk['timestamp'],
                            'transaction_hash': chunk.get('transaction_hash', ''),
                            'status': 'ready' if is_available else 'unavailable'
                        }
                        if is_available:
                            chunk_data['video_url'] = ipfs_handler.get_ipfs_url(chunk['video_cid'])
                        chunks.append(chunk_data)
                        app.logger.info(f"Chunk {chunk['video_cid']} status: {'available' if is_available else 'unavailable'}")
                    except Exception as e:
                        app.logger.error(f"Error processing chunk: {str(e)}")
                        chunks.append({
                            'video_cid': chunk.get('video_cid', ''),
                            'sequence_number': chunk.get('sequence_number', 0),
                            'status': 'error',
                            'error': str(e)
                        })
                
                # Sort chunks by sequence number
                session['chunks'] = sorted(chunks, key=lambda x: x['sequence_number'])
                
            except Exception as e:
                app.logger.error(f"Error processing session {session_id}: {str(e)}")
                session['status'] = 'error'
                session['error'] = str(e)
        
        return jsonify({'sessions': sessions})
        
    except Exception as e:
        app.logger.error(f"Error getting video sessions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/video-sessions/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    """Get status of a specific video session"""
    try:
        status = dashcam_manager.get_status()
        if status.get('session_id') == int(session_id):
            return jsonify(status)
        
        # Session not active, get from blockchain
        session = blockchain_handler.get_video_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
            
        return jsonify(session)
        
    except Exception as e:
        app.logger.error(f"Error getting session status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/dashcam/start', methods=['POST'])
def start_recording():
    """Start dashcam recording"""
    try:
        if dashcam_manager.is_recording:
            return jsonify({'error': 'Recording already in progress'}), 400
            
        success = dashcam_manager.start_recording()
        if not success:
            return jsonify({
                'error': 'Failed to start recording',
                'details': dashcam_manager.last_error
            }), 500
            
        return jsonify({
            'status': 'started',
            'session_id': dashcam_manager.session_id
        })
        
    except Exception as e:
        app.logger.error(f"Error starting recording: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/dashcam/stop', methods=['POST'])
def stop_recording():
    """Stop dashcam recording"""
    try:
        if not dashcam_manager.is_recording:
            return jsonify({'error': 'No recording in progress'}), 400
            
        session_id = dashcam_manager.session_id
        dashcam_manager.stop_recording()
        
        return jsonify({
            'status': 'stopped',
            'session_id': session_id,
            'error_count': dashcam_manager.error_count,
            'last_error': dashcam_manager.last_error
        })
        
    except Exception as e:
        app.logger.error(f"Error stopping recording: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/dashcam/status', methods=['GET'])
def get_recording_status():
    """Get current recording status"""
    try:
        status = dashcam_manager.get_status()
        return jsonify(status)
        
    except Exception as e:
        app.logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashcam/preview', methods=['GET'])
def get_preview_stream():
    """Get video preview stream"""
    try:
        def generate_frames():
            while dashcam_manager.is_recording:
                frame = dashcam_manager.recorder.get_preview_frame()
                if frame is not None:
                    # Encode frame to JPEG
                    ret, buffer = cv2.imencode('.jpg', frame)
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(1/30)  # 30 FPS

        return Response(
            generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        app.logger.error(f"Error in preview stream: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashcam/latest-chunk', methods=['GET'])
def get_latest_chunk():
    """Get latest recorded chunk URL"""
    try:
        if not dashcam_manager.is_recording:
            return jsonify({
                'status': 'error',
                'message': 'Not recording'
            }), 400

        latest = dashcam_manager.get_latest_chunk()
        if latest:
            return jsonify({
                'status': 'success',
                'data': {
                    'video_url': f"{ipfs_handler.ipfs_gateway}/ipfs/{latest['video_cid']}",
                    'metadata_url': f"{ipfs_handler.ipfs_gateway}/ipfs/{latest['metadata_cid']}",
                    'sequence_number': latest['sequence_number']
                }
            })
        return jsonify({
            'status': 'error',
            'message': 'No chunks available'
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/dashcam/chunk', methods=['POST'])
def upload_chunk():
    """Handle video chunk upload"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
            
        video_file = request.files['video']
        session_id = request.form.get('session_id')
        timestamp = request.form.get('timestamp')
        
        if not session_id:
            return jsonify({'error': 'No session ID provided'}), 400
            
        # Create chunk metadata
        metadata = {
            'timestamp': timestamp,
            'session_id': session_id,
            'content_type': video_file.content_type,
            'size': len(video_file.read())
        }
        video_file.seek(0)  # Reset file pointer after reading
        
        # Create chunk object
        chunk = VideoChunk(
            start_time=float(timestamp)/1000 if timestamp else time.time(),
            data=video_file.read(),
            sequence_number=dashcam_manager.current_chunk,
            metadata=metadata
        )
        
        # Add to upload queue
        dashcam_manager.add_chunk(chunk)
        
        return jsonify({
            'status': 'success',
            'chunk_number': chunk.sequence_number
        })
        
    except Exception as e:
        app.logger.error(f"Error handling chunk upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

def cleanup():
    """Cleanup resources on shutdown"""
    try:
        camera.cleanup()
        ipfs_handler.cleanup()
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    try:
        # Create required directories
        Path("captures").mkdir(exist_ok=True)
        
        # Start the Flask app
        port = int(os.getenv('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=not IS_RASPBERRY_PI)
    finally:
        cleanup() 