#!/usr/bin/env python3
"""
Runner script for CASA-Lite
A computer vision-based tool for fish sperm motility analysis
"""

import sys
import os
import argparse

# Ensure the package is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CASA-Lite: Computer-Assisted Sperm Analysis Tool")
    parser.add_argument("--video", type=str, help="Path to input video file")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    parser.add_argument("--web", action="store_true", help="Start web interface")
    parser.add_argument("--debug", action="store_true", default=True, help="Enable debug mode")
    parser.add_argument("--max-frames", type=int, default=300, help="Maximum number of frames to process")
    
    args = parser.parse_args()
    main(args) 