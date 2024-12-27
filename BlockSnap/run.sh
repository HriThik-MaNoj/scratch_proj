#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print with color
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check for required dependencies
check_dependencies() {
    print_status "$YELLOW" "Checking dependencies..."
    
    # Check for conda
    if ! command_exists conda; then
        print_status "$RED" "Error: conda is not installed. Please install Miniconda or Anaconda first."
        exit 1
    fi
    
    # Check for IPFS
    if ! command_exists ipfs; then
        print_status "$RED" "Error: IPFS is not installed. Please install IPFS first."
        exit 1
    fi
    
    # Check for Node.js and npm
    if ! command_exists node || ! command_exists npm; then
        print_status "$RED" "Error: Node.js and npm are required. Please install them first."
        exit 1
    fi
    
    print_status "$GREEN" "All dependencies found!"
}

# Function to check if a process is running on a port
is_port_in_use() {
    lsof -i:"$1" >/dev/null 2>&1
}

# Function to kill process on a specific port
kill_port_process() {
    local port=$1
    if is_port_in_use "$port"; then
        print_status "$YELLOW" "Port $port is in use. Attempting to free it..."
        fuser -k "$port"/tcp
        sleep 2
    fi
}

# Setup environment
setup_environment() {
    print_status "$YELLOW" "Setting up conda environment..."
    
    # Check if environment exists
    if ! conda env list | grep -q "blocksnap"; then
        print_status "$YELLOW" "Creating conda environment 'blocksnap'..."
        conda create -n blocksnap python=3.11 -y
    fi
    
    # Activate environment and install dependencies
    print_status "$YELLOW" "Installing Python dependencies..."
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate blocksnap
    pip install -r requirements.txt
    
    # Install npm dependencies
    print_status "$YELLOW" "Installing Node.js dependencies..."
    cd frontend && npm install && cd ..
}

# Start IPFS daemon
start_ipfs() {
    print_status "$YELLOW" "Starting IPFS daemon..."
    if pgrep -x "ipfs" >/dev/null; then
        print_status "$YELLOW" "IPFS daemon is already running"
    else
        ipfs daemon &
        sleep 5 # Wait for IPFS to start
    fi
}

# Start backend server
start_backend() {
    print_status "$YELLOW" "Starting backend server..."
    kill_port_process 5000
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate blocksnap
    python main.py &
    sleep 5 # Wait for backend to start
}

# Start frontend
start_frontend() {
    print_status "$YELLOW" "Starting frontend..."
    kill_port_process 3000
    cd frontend
    npm start &
    cd ..
}

# Main execution
main() {
    print_status "$GREEN" "Starting BlockSnap..."
    
    # Check dependencies
    check_dependencies
    
    # Setup environment if needed
    if [ "$1" == "--setup" ]; then
        setup_environment
    fi
    
    # Start all services
    start_ipfs
    start_backend
    start_frontend
    
    print_status "$GREEN" "BlockSnap is running!"
    print_status "$GREEN" "Frontend: http://localhost:3000"
    print_status "$GREEN" "Backend: http://localhost:5000"
    print_status "$GREEN" "IPFS Gateway: http://localhost:8080"
    print_status "$YELLOW" "Press Ctrl+C to stop all services"
    
    # Wait for Ctrl+C
    trap 'cleanup' INT
    wait
}

# Cleanup function
cleanup() {
    print_status "$YELLOW" "Shutting down services..."
    pkill -f "ipfs daemon"
    pkill -f "python main.py"
    pkill -f "node.*start"
    print_status "$GREEN" "Cleanup complete. Goodbye!"
    exit 0
}

# Run the script
if [ "$1" == "--help" ]; then
    echo "Usage: ./run.sh [--setup]"
    echo "  --setup: First-time setup (create conda env and install dependencies)"
    echo "  --help:  Show this help message"
else
    main "$1"
fi
