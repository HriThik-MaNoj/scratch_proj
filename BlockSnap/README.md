# BlockSnap - Decentralized Camera System

BlockSnap is a decentralized camera system that captures photos, stores them on IPFS, and mints NFTs to prove ownership and authenticity. The project is integrated with the BuildBear network for blockchain interactions.

## Features

- Capture photos through web interface
- Store photos on IPFS (local node or Pinata)
- Mint NFTs for each photo
- View NFT gallery with IPFS integration
- Copy IPFS CIDs directly from the gallery
- Blockchain verification of photo authenticity

## Prerequisites

- Python 3.11 or higher
- Node.js and npm
- IPFS daemon running locally
- Conda (for environment management)
- MetaMask wallet

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd BlockSnap
```

2. Create and activate Conda environment:
```bash
conda create -n blocksnap python=3.11
conda activate blocksnap
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install Node.js dependencies:
```bash
npm install
```

5. Start IPFS daemon:
```bash
ipfs daemon
```

6. Configure environment variables:
```bash
cp .env.example .env
```
Edit `.env` file with your configuration:
```env
# Ethereum Network Configuration
ETH_RPC_URL=https://rpc.buildbear.io/impossible-omegared-15eaf7dd
CONTRACT_ADDRESS=<your-contract-address>
PRIVATE_KEY=<your-private-key>

# IPFS Configuration
IPFS_HOST=http://127.0.0.1:5001
IPFS_GATEWAY=http://127.0.0.1:8080
USE_PINATA=false

# Optional Pinata Configuration
PINATA_API_KEY=
PINATA_SECRET_KEY=
```

## Quick Start with Automated Script

We provide an automated script to simplify the startup process:

1. **First-time setup:**
   ```bash
   ./run.sh --setup
   ```
   This will:
   - Create the conda environment
   - Install Python dependencies
   - Install Node.js dependencies

2. **Regular startup:**
   ```bash
   ./run.sh
   ```
   This will automatically:
   - Start IPFS daemon
   - Start the Flask backend server
   - Launch the React frontend
   - Set up all necessary connections

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:5000
   - IPFS Gateway: http://localhost:8080

4. **Stop all services:**
   - Press Ctrl+C in the terminal running the script
   - The script will gracefully shut down all services

The script includes:
- Dependency checks
- Environment setup
- Port management
- Process cleanup
- Error handling

## Smart Contract Deployment

1. Compile the smart contract:
```bash
npx hardhat clean
npx hardhat compile
```

2. Deploy to BuildBear network:
```bash
npx hardhat run scripts/deploy.js --network buildbear
```

3. Update the `CONTRACT_ADDRESS` in `.env` with the newly deployed contract address

## Running the Application

1. Start the backend server:
```bash
conda activate blocksnap
/home/hrithik/miniconda3/envs/blocksnap/bin/python main.py
```

2. Start the frontend development server:
```bash
npm start
```

3. Access the application at `http://localhost:3000`

## Usage

1. Connect your MetaMask wallet
2. Navigate to the Camera page
3. Capture a photo or upload one
4. The photo will be:
   - Stored on IPFS
   - Minted as an NFT
   - Displayed in your gallery
5. View your NFTs in the Gallery page
6. Copy IPFS CIDs using the copy button next to each NFT

## Architecture

- Frontend: React.js with Chakra UI
- Backend: Flask
- Blockchain: Solidity smart contract on BuildBear network
- Storage: IPFS (local node or Pinata)

## Smart Contract

The `BlockSnapNFT` contract (`smart_contracts/BlockSnapNFT.sol`) implements:
- ERC721 standard for NFTs
- Photo ownership verification
- IPFS CID storage
- Metadata URI management

## API Endpoints

- `POST /capture`: Capture and mint a new photo NFT
- `GET /nfts/<wallet_address>`: Get all NFTs owned by a wallet
- `GET /health`: Health check endpoint

## Development

- Backend code is in the `backend/` directory
- Frontend code is in the `frontend/` directory
- Smart contracts are in `smart_contracts/`
- Tests are in the `test/` directory

## Security

- Private keys and API keys should be kept secure
- Use environment variables for sensitive data
- Never commit `.env` file to version control

## Troubleshooting

1. IPFS Connection Issues:
   - Ensure IPFS daemon is running
   - Check IPFS host and gateway configurations
   - Verify IPFS ports are accessible

2. Smart Contract Issues:
   - Verify contract deployment
   - Check BuildBear network connection
   - Ensure wallet has sufficient funds

3. Image Display Issues:
   - Check IPFS gateway accessibility
   - Verify image CIDs are valid
   - Ensure frontend has correct gateway URL

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License](LICENSE)
