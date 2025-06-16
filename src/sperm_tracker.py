"""
Sperm tracking module for the Automated Sperm Analysis System
"""

import cv2
import numpy as np
import logging
import math
import time
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class SpermTrack:
    """Class for storing sperm tracking data"""
    id: int
    positions: List[Tuple[int, int]]
    frame_indices: List[int]
    velocities: List[float]
    
    @property
    def total_distance(self) -> float:
        """Calculate total distance traveled"""
        if len(self.positions) < 2:
            return 0.0
            
        dist = 0.0
        for i in range(1, len(self.positions)):
            x1, y1 = self.positions[i-1]
            x2, y2 = self.positions[i]
            dist += math.sqrt((x2-x1)**2 + (y2-y1)**2)
        return dist
        
    @property
    def straight_line_distance(self) -> float:
        """Calculate straight-line distance from first to last position"""
        if len(self.positions) < 2:
            return 0.0
            
        x1, y1 = self.positions[0]
        x2, y2 = self.positions[-1]
        return math.sqrt((x2-x1)**2 + (y2-y1)**2)
        
    @property
    def linearity(self) -> float:
        """Calculate path linearity (straight line / total distance)"""
        total = self.total_distance
        if total == 0:
            return 0.0
        return self.straight_line_distance / total
        
    @property
    def avg_velocity(self) -> float:
        """Calculate average velocity"""
        if not self.velocities:
            return 0.0
        return sum(self.velocities) / len(self.velocities)


class SpermTracker:
    """
    Detects and tracks individual sperm cells across video frames
    """
    
    def __init__(self, min_area=10, max_area=200, detection_threshold=20, max_disappeared=5, debug=False):
        """
        Initialize the sperm tracker
        
        Args:
            min_area (int): Minimum contour area to be considered a sperm
            max_area (int): Maximum contour area to be considered a sperm
            detection_threshold (int): Threshold for detecting sperm cells
            max_disappeared (int): Maximum number of frames a sperm can disappear before track is terminated
            debug (bool): Enable debug mode with visualizations
        """
        self.min_area = min_area
        self.max_area = max_area
        self.detection_threshold = detection_threshold
        self.max_disappeared = max_disappeared
        self.debug = debug
        self.next_id = 0
        self.tracks = {}  # Dictionary of active tracks: {track_id: SpermTrack}
        self.disappeared = {}  # Dictionary to track disappeared sperm: {track_id: frames_disappeared}
        self.frame_index = 0
        
        # Parameters for tracking
        self.max_distance = 50  # Maximum distance for frame-to-frame tracking
        
        # Performance settings
        self.max_detections = 50  # Maximum number of detections per frame
        self.max_active_tracks = 200  # Maximum number of active tracks to maintain
        self.process_delay = 0.01  # Delay between frames to prevent CPU overload
        
        # Setup logging
        level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def track_sperm(self, frames):
        """
        Track sperm across video frames
        
        Args:
            frames (list): List of preprocessed frames
            
        Returns:
            list: List of SpermTrack objects
        """
        if not frames:
            self.logger.error("No frames provided for tracking")
            return []
            
        completed_tracks = []
        self.frame_index = 0
        self.tracks = {}
        self.disappeared = {}
        self.next_id = 0
        
        total_frames = len(frames)
        self.logger.info(f"Starting sperm tracking on {total_frames} frames")
        
        try:
            # Process every frame
            for frame_data in frames:
                # Check if frame data is valid
                if 'binary' not in frame_data or frame_data['binary'] is None:
                    self.logger.warning(f"Invalid frame data at index {self.frame_index}")
                    self.frame_index += 1
                    continue
                    
                binary = frame_data['binary']
                original = frame_data['original']
                
                # Detect sperm in current frame
                sperm_positions = self._detect_sperm(binary)
                
                # Update tracking
                self._update_tracks(sperm_positions)
                
                # Check for disappeared tracks
                completed = self._handle_disappeared()
                completed_tracks.extend(completed)
                
                # Limit the number of active tracks for performance
                if len(self.tracks) > self.max_active_tracks:
                    self._prune_tracks()
                
                # Debug visualization
                if self.debug:
                    debug_frame = original.copy()
                    self._draw_tracks(debug_frame)
                    cv2.imshow("Tracking", debug_frame)
                    cv2.waitKey(1)
                
                self.frame_index += 1
                if self.frame_index % 10 == 0 or self.frame_index == total_frames:
                    self.logger.info(f"Processed {self.frame_index}/{total_frames} frames, {len(self.tracks)} active tracks")
                    
                # Add a small delay to prevent CPU overload
                time.sleep(self.process_delay)
            
            # Add remaining tracks to completed list
            for track_id, track in self.tracks.items():
                completed_tracks.append(track)
                
            self.logger.info(f"Tracking complete. Found {len(completed_tracks)} tracks.")
            return completed_tracks
            
        except Exception as e:
            self.logger.error(f"Error during tracking: {str(e)}")
            # Return any tracks we've found so far
            for track_id, track in self.tracks.items():
                completed_tracks.append(track)
            return completed_tracks
    
    def _detect_sperm(self, binary_frame):
        """
        Detect sperm cells in binary frame
        
        Args:
            binary_frame (numpy.ndarray): Binary image
            
        Returns:
            list: List of (x, y) centroid positions
        """
        try:
            contours, _ = cv2.findContours(binary_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            positions = []
            
            # Limit the number of contours to process for performance
            max_contours = 100
            if len(contours) > max_contours:
                self.logger.warning(f"Too many contours ({len(contours)}), limiting to {max_contours}")
                # Sort by area and take the largest ones
                contours = sorted(contours, key=cv2.contourArea, reverse=True)[:max_contours]
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter by area
                if self.min_area <= area <= self.max_area:
                    M = cv2.moments(contour)
                    
                    # Calculate centroid
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        positions.append((cx, cy))
            
            # Limit the number of detections
            if len(positions) > self.max_detections:
                self.logger.warning(f"Too many detections ({len(positions)}), limiting to {self.max_detections}")
                positions = positions[:self.max_detections]
                
            return positions
            
        except Exception as e:
            self.logger.error(f"Error during detection: {str(e)}")
            return []
    
    def _update_tracks(self, current_positions):
        """
        Update tracks with new positions
        
        Args:
            current_positions (list): List of current sperm positions
        """
        # If no tracks yet, initialize with current positions
        if not self.tracks:
            for position in current_positions:
                self._create_new_track(position)
            return
            
        # If no current positions, mark all as disappeared
        if not current_positions:
            for track_id in list(self.tracks.keys()):
                self._mark_disappeared(track_id)
            return
            
        # Calculate distances between current positions and existing tracks
        track_ids = list(self.tracks.keys())
        track_positions = [self.tracks[track_id].positions[-1] for track_id in track_ids]
        
        # Create distance matrix
        distances = np.zeros((len(track_positions), len(current_positions)))
        for i, track_pos in enumerate(track_positions):
            for j, current_pos in enumerate(current_positions):
                distances[i, j] = math.sqrt((track_pos[0] - current_pos[0])**2 + 
                                           (track_pos[1] - current_pos[1])**2)
        
        # Find assignments using greedy approach (for speed)
        assigned_tracks = set()
        assigned_positions = set()
        assignments = []
        
        # Sort all distances and assign greedily
        flat_indices = np.argsort(distances.flatten())
        for idx in flat_indices:
            i, j = np.unravel_index(idx, distances.shape)
            
            # Skip if already assigned or distance too large
            if i in assigned_tracks or j in assigned_positions or distances[i, j] > self.max_distance:
                continue
                
            # Assign track to position
            assignments.append((track_ids[i], current_positions[j]))
            assigned_tracks.add(i)
            assigned_positions.add(j)
            
            # If all tracks or positions assigned, break
            if len(assigned_tracks) == len(track_ids) or len(assigned_positions) == len(current_positions):
                break
        
        # Update assigned tracks
        for track_id, position in assignments:
            self._update_track(track_id, position)
            
        # Mark unassigned tracks as disappeared
        for i, track_id in enumerate(track_ids):
            if i not in assigned_tracks:
                self._mark_disappeared(track_id)
                
        # Create new tracks for unassigned positions
        for j, position in enumerate(current_positions):
            if j not in assigned_positions:
                self._create_new_track(position)
    
    def _prune_tracks(self):
        """Prune tracks to maintain performance"""
        if len(self.tracks) <= self.max_active_tracks:
            return
            
        # Sort tracks by length (shorter tracks are less reliable)
        sorted_tracks = sorted(
            self.tracks.items(),
            key=lambda x: len(x[1].positions)
        )
        
        # Remove the shortest tracks
        tracks_to_remove = len(self.tracks) - self.max_active_tracks
        for i in range(tracks_to_remove):
            track_id = sorted_tracks[i][0]
            del self.tracks[track_id]
            if track_id in self.disappeared:
                del self.disappeared[track_id]
    
    def _create_new_track(self, position):
        """Create a new track"""
        track = SpermTrack(
            id=self.next_id,
            positions=[position],
            frame_indices=[self.frame_index],
            velocities=[]
        )
        self.tracks[self.next_id] = track
        self.next_id += 1
    
    def _update_track(self, track_id, position):
        """Update an existing track with a new position"""
        track = self.tracks[track_id]
        
        # Calculate velocity
        if len(track.positions) > 0:
            prev_x, prev_y = track.positions[-1]
            curr_x, curr_y = position
            distance = math.sqrt((curr_x - prev_x)**2 + (curr_y - prev_y)**2)
            # If frames are not consecutive, adjust velocity calculation
            frame_diff = self.frame_index - track.frame_indices[-1]
            velocity = distance / max(1, frame_diff)
            track.velocities.append(velocity)
        
        # Update track
        track.positions.append(position)
        track.frame_indices.append(self.frame_index)
        
        # Reset disappeared counter if it exists
        if track_id in self.disappeared:
            del self.disappeared[track_id]
    
    def _mark_disappeared(self, track_id):
        """Mark a track as disappeared"""
        if track_id not in self.disappeared:
            self.disappeared[track_id] = 1
        else:
            self.disappeared[track_id] += 1
    
    def _handle_disappeared(self):
        """Handle disappeared tracks and return completed tracks"""
        completed_tracks = []
        
        for track_id in list(self.disappeared.keys()):
            # If track has been gone too long, remove it
            if self.disappeared[track_id] > self.max_disappeared:
                track = self.tracks.pop(track_id)
                del self.disappeared[track_id]
                
                # Only keep tracks that have enough points
                if len(track.positions) >= 3:
                    completed_tracks.append(track)
        
        return completed_tracks
    
    def _draw_tracks(self, frame):
        """Draw tracks on debug frame"""
        for track_id, track in self.tracks.items():
            # Draw track path
            positions = track.positions
            if len(positions) > 1:
                for i in range(1, len(positions)):
                    cv2.line(frame, positions[i-1], positions[i], (0, 255, 0), 1)
                    
            # Draw current position
            if positions:
                cv2.circle(frame, positions[-1], 3, (0, 0, 255), -1)
                cv2.putText(frame, str(track_id), positions[-1], 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1) 