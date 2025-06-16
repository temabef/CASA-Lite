#!/usr/bin/env python3
"""
Optimization script for CASA-Lite on Render's free tier
Run this script to apply performance optimizations for cloud deployment
"""

import os
import re
import sys
import shutil

def backup_file(file_path):
    """Create a backup of a file before modifying it"""
    backup_path = file_path + '.bak'
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")

def modify_file(file_path, replacements):
    """Make replacements in a file"""
    # Create backup
    backup_file(file_path)
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Apply replacements
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Write modified content
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Modified: {file_path}")

def optimize_main_py():
    """Optimize src/main.py - Disable debug mode in production"""
    file_path = 'src/main.py'
    replacements = [
        (
            "def start_web_app(host='0.0.0.0', port=5000, debug=True):",
            "def start_web_app(host='0.0.0.0', port=5000, debug=False):"
        )
    ]
    modify_file(file_path, replacements)

def optimize_app_fixed_py():
    """Optimize src/app_fixed.py - Add memory optimizations and favicon route"""
    file_path = 'src/app_fixed.py'
    
    # Define replacements
    replacements = [
        # Reduce max frames
        (
            "app.config['MAX_FRAMES'] = 30  # Default max frames to process",
            "app.config['MAX_FRAMES'] = 15  # Default max frames to process (reduced for cloud deployment)"
        ),
        # Add favicon route (look for specific location to add it)
        (
            "@app.route('/about')\ndef about():",
            "@app.route('/favicon.ico')\ndef favicon():\n    \"\"\"Serve favicon to avoid 404 errors\"\"\"\n    return send_from_directory(os.path.join(app.root_path, '..', 'static'),\n                               'favicon.ico', mimetype='image/vnd.microsoft.icon')\n\n@app.route('/about')\ndef about():"
        ),
        # Optimize cleanup frequency
        (
            "def before_request():\n    # Store the day timestamp in the app context\n    day_timestamp = int(time.time() / 86400)  # Current day (86400 seconds in a day)\n    \n    # Only run cleanup once per day to avoid performance impact\n    if not hasattr(app, 'last_cleanup_day') or app.last_cleanup_day < day_timestamp:\n        app.last_cleanup_day = day_timestamp",
            "def before_request():\n    # Store the hour timestamp in the app context\n    hour_timestamp = int(time.time() / 3600)  # Current hour (3600 seconds in an hour)\n    \n    # Run cleanup once per hour for cloud deployment\n    if not hasattr(app, 'last_cleanup_hour') or app.last_cleanup_hour < hour_timestamp:\n        app.last_cleanup_hour = hour_timestamp"
        ),
        # Optimize cleanup age
        (
            "cleanup_thread = threading.Thread(target=cleanup_old_files)",
            "cleanup_thread = threading.Thread(target=lambda: cleanup_old_files(max_age_hours=1))"
        ),
        # Optimize trajectory visualization with lower DPI
        (
            "plt.savefig(img_path, dpi=150)",
            "plt.savefig(img_path, dpi=100, format='png', bbox_inches='tight', pad_inches=0.1, optimize=True)"
        ),
        # Optimize velocity visualization with lower DPI
        (
            "plt.savefig(img_path, dpi=150)",
            "plt.savefig(img_path, dpi=100, format='png', bbox_inches='tight', pad_inches=0.1, optimize=True)"
        ),
        # Reduce figure size for trajectory visualization
        (
            "plt.figure(figsize=(10, 8))",
            "plt.figure(figsize=(8, 6))"
        ),
        # Reduce figure size for velocity visualization
        (
            "fig, ax = plt.subplots(1, 3, figsize=(15, 5))",
            "fig, ax = plt.subplots(1, 3, figsize=(12, 4))"
        )
    ]
    
    modify_file(file_path, replacements)

def optimize_video_processor_py():
    """Optimize src/video_processor.py - Add memory monitoring"""
    file_path = 'src/video_processor.py'
    
    # Define replacements for video processor
    replacements = [
        # Add memory monitoring to extract_frames
        (
            "def extract_frames(self, max_frames=None):\n        \"\"\"\n        Extract frames from the video\n        \n        Args:\n            max_frames (int, optional): Maximum number of frames to extract\n            \n        Returns:\n            list: List of preprocessed frames\n        \"\"\"\n        if not self.cap or not self.cap.isOpened():\n            if not self.open_video():\n                return []\n        \n        frames = []\n        frame_count = 0\n        process_limit = min(max_frames if max_frames else self.max_frames, self.frame_count)",
            
            "def extract_frames(self, max_frames=None):\n        \"\"\"\n        Extract frames from the video\n        \n        Args:\n            max_frames (int, optional): Maximum number of frames to extract\n            \n        Returns:\n            list: List of preprocessed frames\n        \"\"\"\n        if not self.cap or not self.cap.isOpened():\n            if not self.open_video():\n                return []\n        \n        # Monitor available memory\n        available_memory = psutil.virtual_memory().available / (1024 * 1024)  # in MB\n        \n        frames = []\n        frame_count = 0\n        \n        # Adjust frame processing based on available memory\n        if available_memory < 100:  # Less than 100MB available\n            process_limit = min(max_frames if max_frames else 10, self.frame_count)\n            self.logger.warning(f\"Low memory ({available_memory:.1f}MB). Reducing processing to {process_limit} frames\")\n        else:\n            process_limit = min(max_frames if max_frames else self.max_frames, self.frame_count)"
        ),
        
        # Optimize frame step calculation for better performance
        (
            "def _get_optimal_frame_step(self, max_frames):\n        \"\"\"Calculate optimal frame step based on video length and max frames\"\"\"\n        if self.frame_count <= max_frames:\n            return 1\n        \n        # For very long videos, ensure we sample from beginning, middle and end\n        if self.frame_count > max_frames * 10:\n            return max(1, self.frame_count // max_frames)\n        \n        # For moderately long videos, use a more balanced approach\n        return max(1, int(self.frame_count / max_frames))",
            
            "def _get_optimal_frame_step(self, max_frames):\n        \"\"\"Calculate optimal frame step based on video length and max frames\"\"\"\n        if self.frame_count <= max_frames:\n            return 1\n        \n        # For cloud deployment, be more aggressive with frame skipping\n        if self.frame_count > max_frames * 5:\n            return max(1, self.frame_count // max_frames)\n        \n        # For moderately long videos, use a more balanced approach\n        return max(1, int(self.frame_count / max_frames))"
        )
    ]
    
    modify_file(file_path, replacements)

def create_favicon():
    """Create a simple favicon if one doesn't exist"""
    favicon_path = 'static/favicon.ico'
    if os.path.exists(favicon_path):
        print(f"Favicon already exists at {favicon_path}")
        return
    
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from PIL import Image
        
        # Create a simple favicon
        plt.figure(figsize=(1, 1), dpi=16)
        plt.axis('off')
        circle = plt.Circle((0.5, 0.5), 0.4, color='#3498db')
        plt.gca().add_patch(circle)
        plt.gca().set_aspect('equal')
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        
        # Save as PNG first
        temp_path = 'static/temp_favicon.png'
        plt.savefig(temp_path, format='png', transparent=False)
        plt.close()
        
        # Convert to ICO
        img = Image.open(temp_path)
        img.save(favicon_path, format='ICO', sizes=[(16, 16)])
        
        # Clean up temporary file
        os.remove(temp_path)
        print(f"Created favicon at {favicon_path}")
    except ImportError as e:
        print(f"Could not create favicon: {e}")
        print("Please create a favicon manually and save it at static/favicon.ico")

def main():
    """Apply all optimizations"""
    print("Applying optimizations for Render deployment...")
    
    # Ensure we're in the correct directory
    if not os.path.exists('src/app_fixed.py'):
        print("Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Apply optimizations
    optimize_main_py()
    optimize_app_fixed_py()
    optimize_video_processor_py()
    create_favicon()
    
    print("\nAll optimizations applied successfully!")
    print("Please test locally before pushing to GitHub.")
    print("Push the changes to GitHub with: git add . && git commit -m \"Optimize for Render deployment\" && git push origin master")

if __name__ == "__main__":
    main() 