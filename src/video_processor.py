"""
Video processing module for the Automated Sperm Analysis System
"""

import cv2
import numpy as np
from pathlib import Path
import logging

class VideoProcessor:
    """
    Handles video input and preprocessing for sperm analysis
    """
    
    def __init__(self, video_path, debug=False):
        """
        Initialize the video processor
        
        Args:
            video_path (str): Path to the input video file
            debug (bool): Enable debug mode with visualizations
        """
        self.video_path = video_path
        self.debug = debug
        self.cap = None
        self.frame_count = 0
        self.fps = 0
        self.width = 0
        self.height = 0
        
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging configuration"""
        level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def open_video(self):
        """Open the video file and get basic properties"""
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
    
    def extract_frames(self, max_frames=None):
        """
        Extract frames from the video
        
        Args:
            max_frames (int, optional): Maximum number of frames to extract
            
        Returns:
            list: List of preprocessed frames
        """
        if not self.open_video():
            return []
        
        frames = []
        frame_count = 0
        process_limit = max_frames if max_frames else self.frame_count
        
        self.logger.info(f"Extracting {process_limit} frames")
        
        while frame_count < process_limit:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            # Preprocess the frame (apply filters, enhance contrast)
            processed = self.preprocess_frame(frame)
            
            frames.append(processed)
            frame_count += 1
            
            if self.debug and frame_count % 100 == 0:
                self.logger.debug(f"Processed {frame_count}/{process_limit} frames")
                
        self.cap.release()
        self.logger.info(f"Extracted {len(frames)} frames")
        return frames
    
    def preprocess_frame(self, frame):
        """
        Preprocess a single frame for sperm detection
        
        Args:
            frame (numpy.ndarray): Input frame
            
        Returns:
            numpy.ndarray: Preprocessed frame
        """
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
        
        if self.debug:
            # Show preprocessing steps
            debug_frame = np.hstack((gray, enhanced, binary))
            cv2.imshow("Preprocessing", debug_frame)
            cv2.waitKey(1)
            
        return {
            'original': frame,
            'gray': gray,
            'enhanced': enhanced,
            'binary': binary
        }
    
    def sample_frame(self, frame_number=0):
        """
        Extract a specific frame for testing
        
        Args:
            frame_number (int): Frame number to extract
            
        Returns:
            dict: Processed frame data
        """
        if not self.open_video():
            return None
            
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        self.cap.release()
        
        if not ret:
            self.logger.error(f"Failed to extract frame {frame_number}")
            return None
            
        return self.preprocess_frame(frame) 