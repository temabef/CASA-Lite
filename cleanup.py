#!/usr/bin/env python3
"""
Cleanup script to prepare CASA-Lite for deployment
This script removes unnecessary files and cleans up the repository
"""

import os
import shutil
import glob
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_source_duplicates():
    """Remove duplicate source files"""
    files_to_remove = [
        'src/app.py',
        'src/app_clean.py',
        'src/app_fixed_with_viz.py',
        'src/video_processor_new.py',
        'src/temp.txt'
    ]
    
    removed_count = 0
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Removed: {file_path}")
                removed_count += 1
            except Exception as e:
                logger.error(f"Failed to remove {file_path}: {str(e)}")
    
    logger.info(f"Removed {removed_count} duplicate source files")

def cleanup_test_data(keep_one=True):
    """Clean up test data in uploads directory"""
    if not os.path.exists('uploads'):
        logger.info("No uploads directory found")
        return
    
    # Get all video files
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.wmv']
    all_videos = []
    
    for ext in video_extensions:
        all_videos.extend(glob.glob(os.path.join('uploads', ext)))
    
    # Find unique video names (without UUID prefixes)
    unique_videos = {}
    for video_path in all_videos:
        filename = os.path.basename(video_path)
        
        # Check if it has a UUID prefix (assuming UUID_name.ext format)
        if '_' in filename:
            parts = filename.split('_', 1)
            if len(parts[0]) >= 32:  # Rough check for UUID-like string
                base_name = parts[1]
                if base_name not in unique_videos:
                    unique_videos[base_name] = []
                unique_videos[base_name].append(video_path)
        else:
            if filename not in unique_videos:
                unique_videos[filename] = []
            unique_videos[filename].append(video_path)
    
    # Keep one of each unique video if requested
    removed_count = 0
    for base_name, file_paths in unique_videos.items():
        if len(file_paths) > 1:
            to_keep = file_paths[0] if keep_one else None
            
            for path in file_paths:
                if path != to_keep:
                    try:
                        os.remove(path)
                        logger.info(f"Removed duplicate video: {path}")
                        removed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to remove {path}: {str(e)}")
    
    logger.info(f"Removed {removed_count} duplicate test videos")

def cleanup_output():
    """Clean up analysis output files"""
    if not os.path.exists('output'):
        logger.info("No output directory found")
        return
    
    file_count = 0
    for item in os.listdir('output'):
        item_path = os.path.join('output', item)
        try:
            if os.path.isfile(item_path):
                os.remove(item_path)
                file_count += 1
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                file_count += 1
        except Exception as e:
            logger.error(f"Failed to remove {item_path}: {str(e)}")
    
    logger.info(f"Cleaned {file_count} items from output directory")

def cleanup_pycache():
    """Remove __pycache__ directories"""
    pycache_dirs = []
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                pycache_dirs.append(os.path.join(root, dir_name))
    
    count = 0
    for pycache_dir in pycache_dirs:
        try:
            shutil.rmtree(pycache_dir)
            logger.info(f"Removed: {pycache_dir}")
            count += 1
        except Exception as e:
            logger.error(f"Failed to remove {pycache_dir}: {str(e)}")
    
    logger.info(f"Removed {count} __pycache__ directories")

def create_gitignore():
    """Create or update .gitignore file"""
    gitignore_content = """
# CASA-Lite .gitignore

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
dist/
build/
*.egg-info/

# Virtual environments
venv/
env/
ENV/

# IDE files
.idea/
.vscode/
*.swp
*.swo

# Test data and outputs
uploads/*
output/*
!uploads/.gitkeep
!output/.gitkeep

# Log files
*.log
logs/

# OS specific files
.DS_Store
Thumbs.db
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content.strip())
    
    # Create .gitkeep files to keep the directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    
    open('uploads/.gitkeep', 'w').close()
    open('output/.gitkeep', 'w').close()
    
    logger.info("Created/updated .gitignore file")

def main():
    parser = argparse.ArgumentParser(description="Cleanup script for CASA-Lite deployment")
    parser.add_argument('--keep-sample', action='store_true', help="Keep one sample video in uploads")
    parser.add_argument('--all', action='store_true', help="Run all cleanup operations")
    parser.add_argument('--source', action='store_true', help="Clean up duplicate source files")
    parser.add_argument('--uploads', action='store_true', help="Clean up uploads directory")
    parser.add_argument('--output', action='store_true', help="Clean up output directory")
    parser.add_argument('--pycache', action='store_true', help="Clean up __pycache__ directories")
    parser.add_argument('--gitignore', action='store_true', help="Create/update .gitignore file")
    
    args = parser.parse_args()
    
    # If no specific operation specified, show help
    if not any([args.all, args.source, args.uploads, args.output, args.pycache, args.gitignore]):
        parser.print_help()
        return
    
    logger.info("Starting CASA-Lite cleanup process")
    
    if args.all or args.source:
        cleanup_source_duplicates()
    
    if args.all or args.uploads:
        cleanup_test_data(keep_one=args.keep_sample)
    
    if args.all or args.output:
        cleanup_output()
    
    if args.all or args.pycache:
        cleanup_pycache()
    
    if args.all or args.gitignore:
        create_gitignore()
    
    logger.info("Cleanup complete!")

if __name__ == "__main__":
    main() 