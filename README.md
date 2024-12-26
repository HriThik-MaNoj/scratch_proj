# BlockSnap - Blockchain-based Camera System

A decentralized camera system that captures photos using Raspberry Pi, stores them on IPFS, and mints NFTs to prove ownership and authenticity.

## System Architecture

```
BlockSnap/
├── hardware/         # Raspberry Pi camera and GPIO code
├── smart_contracts/  # Solidity contracts for NFT minting
├── backend/         # Python backend for IPFS integration
├── frontend/        # React.js DApp
└── scripts/         # Utility scripts and tools
```

## Features

- Photo capture using Raspberry Pi Camera Module
- Secure storage on IPFS with metadata
- NFT minting on Ethereum (Sepolia testnet)
- Crypto wallet integration (MetaMask)
- Image authenticity verification
- Touchscreen interface for user interaction

## Prerequisites

### Hardware Requirements
- Raspberry Pi 4 or 3B+
- Raspberry Pi Camera Module
- GPIO-connected shutter button
- Touchscreen display (optional)
- GPS Module (optional)

### Software Requirements
- Python 3.8+
- Node.js 16+
- IPFS
- MetaMask wallet
- Ethereum development environment (Hardhat)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/BlockSnap.git
cd BlockSnap
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Node.js dependencies:
```bash
cd frontend
npm install
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Development Setup

### Smart Contract Development
1. Install Hardhat and dependencies
2. Deploy contracts to Sepolia testnet
3. Update contract addresses in configuration

### IPFS Setup
1. Install IPFS daemon
2. Configure IPFS endpoints
3. Set up Pinata account for pinning

### Raspberry Pi Setup
1. Enable camera module
2. Configure GPIO pins
3. Install required system packages

## Usage

1. Start the IPFS daemon:
```bash
ipfs daemon
```

2. Run the backend server:
```bash
python backend/app.py
```

3. Start the frontend development server:
```bash
cd frontend
npm start
```

4. Connect MetaMask wallet and ensure Sepolia testnet is selected

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
