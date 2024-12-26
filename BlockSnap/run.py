#!/usr/bin/env python3

import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Import and run the Flask app
from backend.app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
