"""
Video processing module for the Automated Sperm Analysis System
"""

import cv2
import numpy as np
from pathlib import Path
import logging
import os
import time
import psutil

class VideoProcessor:
    """
    Handles video input and preprocessing for sperm analysis
    """
    
    def __init__(self, video_path=None, max_frames=30, debug=False):
        """
        Initialize the video processor
        
        Args:
            video_path (str, optional): Path to the input video file
            max_frames (int): Maximum number of frames to process
            debug (bool): Enable debug mode with visualizations
        """
        self.video_path = video_path
        self.debug = debug
        self.max_frames = max_frames
        self.cap = None
        self.frame_count = 0
        self.fps = 0
        self.width = 0
        self.height = 0
        
        # Performance settings
        self.max_resolution = (640, 480)  # Maximum resolution to process
        self.cpu_threshold = 90  # CPU usage threshold to slow down processing
        self.process_delay = 0.01  # Small delay to prevent CPU overload
        
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging configuration"""
        level = logging.DEBUG if self.debug else logging.INFO
        self.logger = logging.getLogger(__name__)
    
    def process_video(self, video_path=None):
        """
        Process a video file and extract frames
        
        Args:
            video_path (str, optional): Path to the video file
            
        Returns:
            list: List of preprocessed frames
        """
        if video_path:
            self.video_path = video_path
            
        if not self.video_path or not os.path.exists(self.video_path):
            self.logger.error(f"Video file not found: {self.video_path}")
            return []
            
        if not self.open_video():
            return []
            
        # Extract frames
        frames = self.extract_frames(self.max_frames)
        
        return frames
    
    def open_video(self):
        """Open the video file and get basic properties"""
        if not os.path.exists(self.video_path):
            self.logger.error(f"Error: Video file not found: {self.video_path}")
            return False
            
        try:
            self.logger.info(f"Attempting to open video: {self.video_path}")
            self.cap = cv2.VideoCapture(self.video_path)
            
            if not self.cap.isOpened():
                self.logger.error(f"Error: Could not open video {self.video_path}")
                return False
            
            self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.logger.info(f"Video opened: {self.frame_count} frames, {self.fps} FPS, {self.width}x{self.height}")
            return True
        except Exception as e:
            self.logger.error(f"Exception while opening video: {str(e)}")
            return False
    
    def _get_optimal_frame_step(self, max_frames):
        """Calculate optimal frame step based on video length and max frames"""
        if self.frame_count <= max_frames:
            return 1
        
        # For very long videos, ensure we sample from beginning, middle and end
        if self.frame_count > max_frames * 10:
            return max(1, self.frame_count // max_frames)
        
        # For moderately long videos, use a more balanced approach
        return max(1, int(self.frame_count / max_frames))
    
    def _check_system_resources(self):
        """Check system resources and return True if processing should pause"""
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            if cpu_usage > self.cpu_threshold:
                self.logger.debug(f"High CPU usage detected: {cpu_usage}%, pausing briefly")
                time.sleep(0.5)  # Longer pause when CPU is high
                return True
        except:
            # If psutil is not available, continue without resource checking
            pass
            
        # Add a small delay to prevent CPU overload
        time.sleep(self.process_delay)
        return False
    
    def _get_resize_scale(self, frame):
        """Calculate resize scale for a frame"""
        h, w = frame.shape[:2]
        max_h, max_w = self.max_resolution
        
        # If frame is already smaller than max resolution, return 1.0 (no scaling)
        if h <= max_h and w <= max_w:
            return 1.0
        
        # Calculate scale factor to fit within max resolution
        h_scale = max_h / h if h > max_h else 1.0
        w_scale = max_w / w if w > max_w else 1.0
        
        # Use the smaller scale to ensure both dimensions fit
        return min(h_scale, w_scale)
    
    def extract_frames(self, max_frames=None):
        """
        Extract frames from the video
        
        Args:
            max_frames (int, optional): Maximum number of frames to extract
            
        Returns:
            list: List of preprocessed frames
        """
        if not self.cap or not self.cap.isOpened():
            if not self.open_video():
                return []
        
        frames = []
        frame_count = 0
        process_limit = min(max_frames if max_frames else self.max_frames, self.frame_count)
        
        self.logger.info(f"Extracting {process_limit} frames")
        
        # Calculate frame step to sample evenly across the video
        frame_step = self._get_optimal_frame_step(process_limit)
        self.logger.info(f"Using frame step: {frame_step}")
        
        try:
            # Choose sampling strategy based on video length
            if self.frame_count > 1000 and process_limit < 100:
                # Sample frames from beginning, middle, and end
                sample_points = []
                
                # Beginning frames (40%)
                beginning_count = int(process_limit * 0.4)
                for i in range(beginning_count):
                    sample_points.append(i * frame_step)
                
                # Middle frames (30%)
                middle_count = int(process_limit * 0.3)
                middle_start = self.frame_count // 2 - (middle_count // 2) * frame_step
                for i in range(middle_count):
                    sample_points.append(middle_start + i * frame_step)
                
                # End frames (30%)
                end_count = process_limit - beginning_count - middle_count
                end_start = max(0, self.frame_count - end_count * frame_step)
                for i in range(end_count):
                    sample_points.append(end_start + i * frame_step)
                
                # Sort and remove duplicates
                sample_points = sorted(list(set([min(p, self.frame_count - 1) for p in sample_points])))
                
                # Extract frames at sample points
                for frame_pos in sample_points:
                    if frame_count >= process_limit:
                        break
                    
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                    ret, frame = self.cap.read()
                    
                    if not ret:
                        self.logger.warning(f"Failed to read frame at position {frame_pos}")
                        continue
                    
                    # Process frame
                    processed = self.preprocess_frame(frame)
                    frames.append(processed)
                    frame_count += 1
                    
                    # Check system resources and pause if needed
                    self._check_system_resources()
            else:
                # Standard sequential sampling
                current_frame = 0
                while frame_count < process_limit and current_frame < self.frame_count:
                    # Set position to the next frame to process
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                    
                    ret, frame = self.cap.read()
                    if not ret:
                        self.logger.warning(f"Failed to read frame at position {current_frame}")
                        break
                    
                    # Process frame
                    processed = self.preprocess_frame(frame)
                    frames.append(processed)
                    frame_count += 1
                    current_frame += frame_step
                    
                    if self.debug and frame_count % 5 == 0:
                        self.logger.debug(f"Processed {frame_count}/{process_limit} frames")
                    
                    # Check system resources and pause if needed
                    self._check_system_resources()
                
        except Exception as e:
            self.logger.error(f"Error during frame extraction: {str(e)}")
        finally:
            self.cap.release()
            
        self.logger.info(f"Extracted {len(frames)} frames")
        return frames
    
    def preprocess_frame(self, frame):
        """
        Preprocess a single frame for sperm detection
        
        Args:
            frame (numpy.ndarray): Input frame
            
        Returns:
            dict: Dictionary with processed frame data
        """
        try:
            # Store original frame
            original = frame.copy()
            
            # Resize large frames for better performance
            scale = self._get_resize_scale(frame)
            if scale < 1.0:
                new_size = (int(frame.shape[1] * scale), int(frame.shape[0] * scale))
                frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)
                original = cv2.resize(original, new_size, interpolation=cv2.INTER_AREA)
                self.logger.debug(f"Resized frame to {new_size}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(blurred)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Morphological operations to remove small noise
            kernel = np.ones((3, 3), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
            
            # Return frame data as a dictionary
            return {
                'original': original,
                'gray': gray,
                'enhanced': enhanced,
                'binary': binary
            }
            
        except Exception as e:
            self.logger.error(f"Error preprocessing frame: {str(e)}")
            return None
    
    def sample_frame(self, frame_number=0):
        """
        Sample a single frame from the video
        
        Args:
            frame_number (int): Frame number to sample
            
        Returns:
            dict: Dictionary with processed frame data or None if failed
        """
        if not self.open_video():
            return None
            
        try:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = self.cap.read()
            
            if not ret:
                self.logger.error(f"Could not read frame {frame_number}")
                return None
                
            return self.preprocess_frame(frame)
            
        except Exception as e:
            self.logger.error(f"Error sampling frame: {str(e)}")
            return None
        finally:
            self.cap.release() 