#!/usr/bin/env python3
"""
WSGI entry point for CASA-Lite application
For production deployment with Gunicorn or other WSGI servers
"""

import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask application
from src.app_fixed import app

if __name__ == "__main__":
    app.run() 