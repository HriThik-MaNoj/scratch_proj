#!/usr/bin/env python3

import os
import sys
from pathlib import Path

def setup_environment():
    """Setup the Python environment for BlockSnap."""
    # Add project root to Python path
    project_root = Path(__file__).parent.absolute()
    sys.path.insert(0, str(project_root))
    
    # Create required directories
    Path("captures").mkdir(exist_ok=True)
    
    # Set working directory to project root
    os.chdir(project_root)

if __name__ == "__main__":
    setup_environment()
    
    # Import and run the Flask app
    from backend.app import app
    app.run(host='0.0.0.0', port=5000, debug=True)
