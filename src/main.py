#!/usr/bin/env python3
"""
CASA-Lite: Main Application
A computer vision tool for analyzing fish sperm motility parameters
Developed by Saheed Kolawole
"""

import os
import sys
import cv2
import numpy as np
import argparse
from pathlib import Path

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.video_processor import VideoProcessor
from src.sperm_tracker import SpermTracker
from src.analysis import MotilityAnalyzer
from src.visualization import Visualizer
from src.app import start_web_app

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="CASA-Lite: Computer-Assisted Sperm Analysis Tool")
    parser.add_argument("--video", type=str, help="Path to input video file")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    parser.add_argument("--web", action="store_true", help="Start web interface")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()

def main(args=None):
    """Main function to run the analysis"""
    if args is None:
        args = parse_arguments()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    if args.web:
        print("Starting web interface...")
        start_web_app()
        return
    
    if not args.video:
        print("Error: No video file specified. Use --video to specify a video file or --web to start web interface.")
        return
    
    # Process video file
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        return
    
    print(f"Processing video: {video_path}")
    video_processor = VideoProcessor(str(video_path), debug=args.debug)
    frames = video_processor.extract_frames()
    
    # Track sperm cells
    tracker = SpermTracker(debug=args.debug)
    tracks = tracker.track_sperm(frames)
    
    # Analyze motility
    analyzer = MotilityAnalyzer()
    results = analyzer.analyze(tracks)
    
    # Visualize results
    visualizer = Visualizer(output_dir=str(output_dir))
    visualizer.plot_trajectories(tracks)
    visualizer.plot_velocity_distribution(results)
    report_path = visualizer.generate_report(results)
    
    print(f"Analysis complete. Results saved to {output_dir}")
    print(f"Report available at: {report_path}")
    
if __name__ == "__main__":
    main() 