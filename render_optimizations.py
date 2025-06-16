#!/usr/bin/env python3
"""
Additional optimizations for Render deployment to handle 500 errors
"""

import os
import re
import sys
import shutil

def backup_file(file_path):
    """Create a backup of a file before modifying it"""
    backup_path = file_path + '.bak'
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        print(f"Created backup: {backup_path}")
    else:
        print(f"Backup already exists: {backup_path}")

def modify_file(file_path, replacements):
    """Make replacements in a file"""
    # Create backup
    backup_file(file_path)
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Apply replacements
    modified = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            modified = True
    
    # Write modified content if changes were made
    if modified:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Modified: {file_path}")
    else:
        print(f"No changes needed in: {file_path}")

def add_memory_safeguards():
    """Add memory safeguards to app_fixed.py"""
    file_path = 'src/app_fixed.py'
    
    replacements = [
        # Reduce max frames even further for production
        (
            "app.config['MAX_FRAMES'] = 15",
            "app.config['MAX_FRAMES'] = 10  # Extremely conservative for Render free tier"
        ),
        # Add memory check before processing
        (
            "def analyze():\n    \"\"\"Analyze video and return results\"\"\"\n    if request.method == 'OPTIONS':",
            "def analyze():\n    \"\"\"Analyze video and return results\"\"\"\n    # Check available memory before processing\n    import psutil\n    available_memory = psutil.virtual_memory().available / (1024 * 1024)  # in MB\n    if available_memory < 150:  # Less than 150MB available\n        logger.warning(f\"Low memory before processing: {available_memory:.1f}MB\")\n        return jsonify({\n            'success': False,\n            'error': f\"Server is low on resources. Please try again later. Available memory: {available_memory:.1f}MB\"\n        }), 503\n        \n    if request.method == 'OPTIONS':"
        ),
        # Add explicit garbage collection after processing
        (
            "def analyze():\n    \"\"\"Analyze video and return results\"\"\"\n    if request.method == 'OPTIONS':",
            "def analyze():\n    \"\"\"Analyze video and return results\"\"\"\n    # Import garbage collection\n    import gc\n    \n    if request.method == 'OPTIONS':"
        ),
        # Add garbage collection after processing
        (
            "        return jsonify({\n            'success': True,\n            'summary': summary\n        })",
            "        # Force garbage collection to free memory\n        gc.collect()\n        \n        return jsonify({\n            'success': True,\n            'summary': summary\n        })"
        ),
        # Add extra error handling
        (
            "    except Exception as e:\n        logger.error(f\"Error during analysis: {str(e)}\")\n        logger.error(traceback.format_exc())",
            "    except MemoryError as me:\n        logger.critical(f\"Memory error during analysis: {str(me)}\")\n        # Force garbage collection\n        gc.collect()\n        return jsonify({\n            'success': False,\n            'error': \"Server ran out of memory. Try reducing video length or quality.\"\n        }), 503\n    except Exception as e:\n        logger.error(f\"Error during analysis: {str(e)}\")\n        logger.error(traceback.format_exc())"
        )
    ]
    
    modify_file(file_path, replacements)

def optimize_video_processing():
    """Further optimize video processing for minimal resource usage"""
    file_path = 'src/video_processor.py'
    
    replacements = [
        # Add even more aggressive frame skipping
        (
            "        # Adjust frame processing based on available memory\n        if available_memory < 100:  # Less than 100MB available\n            process_limit = min(max_frames if max_frames else 10, self.frame_count)\n            self.logger.warning(f\"Low memory ({available_memory:.1f}MB). Reducing processing to {process_limit} frames\")",
            "        # Adjust frame processing based on available memory - extremely conservative for Render\n        if available_memory < 150:  # Less than 150MB available\n            process_limit = min(max_frames if max_frames else 5, self.frame_count)\n            self.logger.warning(f\"Low memory ({available_memory:.1f}MB). Reducing processing to {process_limit} frames\")\n        elif available_memory < 250:  # Less than 250MB available\n            process_limit = min(max_frames if max_frames else 10, self.frame_count)\n            self.logger.warning(f\"Limited memory ({available_memory:.1f}MB). Reducing processing to {process_limit} frames\")"
        ),
        # Reduce image size for better performance
        (
            "        # Resize large frames for better performance\n        scale = self._get_resize_scale(frame)\n        if scale < 1.0:\n            new_size = (int(frame.shape[1] * scale), int(frame.shape[0] * scale))\n            frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)\n            original = cv2.resize(original, new_size, interpolation=cv2.INTER_AREA)\n            self.logger.debug(f\"Resized frame to {new_size}\")",
            
            "        # Resize all frames for better performance on Render\n        max_width = 640  # Enforce smaller size for cloud deployment\n        max_height = 480\n        if frame.shape[1] > max_width or frame.shape[0] > max_height:\n            scale = min(max_width / frame.shape[1], max_height / frame.shape[0])\n            new_size = (int(frame.shape[1] * scale), int(frame.shape[0] * scale))\n            frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)\n            original = cv2.resize(original, new_size, interpolation=cv2.INTER_AREA)\n            self.logger.debug(f\"Resized frame to {new_size}\")"
        ),
        # Increase process delay to prevent CPU overload
        (
            "        self.process_delay = 0.01  # Small delay to prevent CPU overload",
            "        self.process_delay = 0.05  # Larger delay for cloud deployment to prevent CPU overload"
        )
    ]
    
    modify_file(file_path, replacements)

def add_timeout_handling():
    """Add better timeout handling to the process.html page"""
    file_path = 'templates/process.html'
    
    replacements = [
        # Increase timeout for Render
        (
            "                const timeoutId = setTimeout(() => controller.abort(), 120000); // 120 seconds timeout",
            "                const timeoutId = setTimeout(() => controller.abort(), 180000); // 180 seconds timeout for Render"
        ),
        # Add more specific error messages for Render
        (
            "                    } else if (error.message.includes(\"timeout\")) {\n                        errorMsg = \"Request timed out. The video processing may be taking too long.\";",
            "                    } else if (error.message.includes(\"timeout\")) {\n                        errorMsg = \"Request timed out. On the free tier, processing may take longer than expected. Try again with a shorter video or reduce the max frames.\";",
        ),
        # Add Render-specific error message
        (
            "                    } else if (error.message.includes(\"JSON\")) {\n                        errorMsg = \"Error processing server response. The server may be returning invalid data.\";",
            "                    } else if (error.message.includes(\"JSON\")) {\n                        errorMsg = \"Error processing server response. The server may be returning invalid data.\";\n                    } else if (error.message.includes(\"503\")) {\n                        errorMsg = \"The server is temporarily unavailable due to resource constraints. This is common on free hosting - please try again in a few minutes.\";"
        )
    ]
    
    modify_file(file_path, replacements)

def main():
    """Apply additional optimizations for Render"""
    print("Applying additional optimizations for Render deployment...")
    
    # Ensure we're in the correct directory
    if not os.path.exists('src/app_fixed.py'):
        print("Error: Please run this script from the project root directory")
        sys.exit(1)
    
    add_memory_safeguards()
    optimize_video_processing()
    add_timeout_handling()
    
    print("\nAdditional optimizations complete!")
    print("Push to GitHub with: git add . && git commit -m \"Further optimize for Render\" && git push origin master")

if __name__ == "__main__":
    main() 