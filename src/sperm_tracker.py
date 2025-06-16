"""
Sperm tracking module for the Automated Sperm Analysis System
"""

import cv2
import numpy as np
import logging
import math
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
    
    def __init__(self, min_area=10, max_area=200, detection_threshold=20, max_disappeared=10, debug=False):
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
        completed_tracks = []
        self.frame_index = 0
        self.tracks = {}
        self.disappeared = {}
        self.next_id = 0
        
        total_frames = len(frames)
        self.logger.info(f"Starting sperm tracking on {total_frames} frames")
        
        for frame_data in frames:
            binary = frame_data['binary']
            original = frame_data['original']
            
            # Detect sperm in current frame
            sperm_positions = self._detect_sperm(binary)
            
            # Update tracking
            self._update_tracks(sperm_positions)
            
            # Check for disappeared tracks
            completed = self._handle_disappeared()
            completed_tracks.extend(completed)
            
            # Debug visualization
            if self.debug:
                debug_frame = original.copy()
                self._draw_tracks(debug_frame)
                cv2.imshow("Tracking", debug_frame)
                cv2.waitKey(1)
            
            self.frame_index += 1
            if self.frame_index % 100 == 0:
                self.logger.info(f"Processed {self.frame_index}/{total_frames} frames, {len(self.tracks)} active tracks")
        
        # Add remaining tracks to completed list
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
        contours, _ = cv2.findContours(binary_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        positions = []
        
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
        
        return positions
    
    def _update_tracks(self, current_positions):
        """
        Update existing tracks with new positions
        
        Args:
            current_positions (list): List of current sperm positions
        """
        if not self.tracks:
            # First frame or all tracks disappeared, create new tracks for all detections
            for pos in current_positions:
                self.tracks[self.next_id] = SpermTrack(
                    id=self.next_id,
                    positions=[pos],
                    frame_indices=[self.frame_index],
                    velocities=[]
                )
                self.disappeared[self.next_id] = 0
                self.next_id += 1
            return
            
        # Calculate distance matrix between current positions and existing tracks
        if not current_positions:
            # No detections in current frame, mark all as disappeared
            for track_id in self.tracks:
                self.disappeared[track_id] += 1
            return
            
        # Get last position of each existing track
        existing_positions = []
        track_ids = []
        
        for track_id, track in self.tracks.items():
            existing_positions.append(track.positions[-1])
            track_ids.append(track_id)
        
        # Calculate distance matrix
        distances = np.zeros((len(existing_positions), len(current_positions)))
        
        for i, pos1 in enumerate(existing_positions):
            for j, pos2 in enumerate(current_positions):
                # Euclidean distance between positions
                dist = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                distances[i, j] = dist
        
        # Assign positions to tracks based on minimum distance
        used_positions = set()
        for i, track_id in enumerate(track_ids):
            if np.min(distances[i, :]) <= self.max_distance:
                # Find closest position
                j = np.argmin(distances[i, :])
                
                # Check if position already used
                if j in used_positions:
                    # Position already assigned to another track
                    self.disappeared[track_id] += 1
                    continue
                    
                # Update track with new position
                pos = current_positions[j]
                track = self.tracks[track_id]
                
                # Calculate velocity
                prev_pos = track.positions[-1]
                dx = pos[0] - prev_pos[0]
                dy = pos[1] - prev_pos[1]
                distance = math.sqrt(dx**2 + dy**2)
                
                if len(track.frame_indices) > 0:
                    frames_passed = self.frame_index - track.frame_indices[-1]
                    if frames_passed > 0:
                        velocity = distance / frames_passed
                        track.velocities.append(velocity)
                
                # Update track
                track.positions.append(pos)
                track.frame_indices.append(self.frame_index)
                self.disappeared[track_id] = 0
                
                # Mark position as used
                used_positions.add(j)
            else:
                # No matching position, mark as disappeared
                self.disappeared[track_id] += 1
        
        # Create new tracks for unused detections
        for j, pos in enumerate(current_positions):
            if j not in used_positions:
                self.tracks[self.next_id] = SpermTrack(
                    id=self.next_id,
                    positions=[pos],
                    frame_indices=[self.frame_index],
                    velocities=[]
                )
                self.disappeared[self.next_id] = 0
                self.next_id += 1
    
    def _handle_disappeared(self):
        """
        Handle disappearance of tracks
        
        Returns:
            list: List of completed SpermTrack objects
        """
        completed = []
        ids_to_remove = []
        
        for track_id, count in self.disappeared.items():
            if count > self.max_disappeared:
                # Track lost for too many frames, consider it completed
                completed.append(self.tracks[track_id])
                ids_to_remove.append(track_id)
        
        # Remove completed tracks
        for track_id in ids_to_remove:
            del self.tracks[track_id]
            del self.disappeared[track_id]
        
        return completed
    
    def _draw_tracks(self, frame):
        """
        Draw tracks on frame for visualization
        
        Args:
            frame (numpy.ndarray): Frame to draw on
        """
        for track_id, track in self.tracks.items():
            # Draw track path
            positions = track.positions
            
            if len(positions) > 1:
                # Draw trail (last 20 positions)
                trail_length = min(20, len(positions))
                for i in range(1, trail_length):
                    p1 = positions[-i]
                    p2 = positions[-(i+1)]
                    # Fade color based on position in trail
                    alpha = 1.0 - (i / trail_length)
                    color = (0, int(255 * alpha), int(255 * (1 - alpha)))
                    cv2.line(frame, p1, p2, color, 1)
            
            # Draw current position
            if positions:
                cv2.circle(frame, positions[-1], 3, (0, 0, 255), -1)
                
                # Display ID
                cv2.putText(
                    frame, 
                    f"#{track_id}", 
                    (positions[-1][0] + 5, positions[-1][1] - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.4, 
                    (0, 255, 0), 
                    1
                )
    
    def track_sperm(self, frames):
        """
        Track sperm across video frames
        
        Args:
            frames (list): List of preprocessed frames
            
        Returns:
            list: List of SpermTrack objects
        """
        completed_tracks = []
        self.frame_index = 0
        self.tracks = {}
        self.disappeared = {}
        self.next_id = 0
        
        total_frames = len(frames)
        self.logger.info(f"Starting sperm tracking on {total_frames} frames")
        
        for frame_data in frames:
            binary = frame_data['binary']
            original = frame_data['original']
            
            # Detect sperm in current frame
            sperm_positions = self._detect_sperm(binary)
            
            # Update tracking
            self._update_tracks(sperm_positions)
            
            # Check for disappeared tracks
            completed = self._handle_disappeared()
            completed_tracks.extend(completed)
            
            # Debug visualization
            if self.debug:
                debug_frame = original.copy()
                self._draw_tracks(debug_frame)
                cv2.imshow("Tracking", debug_frame)
                cv2.waitKey(1)
            
            self.frame_index += 1
            if self.frame_index % 100 == 0:
                self.logger.info(f"Processed {self.frame_index}/{total_frames} frames, {len(self.tracks)} active tracks")
        
        # Add remaining tracks to completed list
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
        contours, _ = cv2.findContours(binary_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        positions = []
        
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
        
        return positions
    
    def _update_tracks(self, current_positions):
        """
        Update existing tracks with new positions
        
        Args:
            current_positions (list): List of current sperm positions
        """
        if not self.tracks:
            # First frame or all tracks disappeared, create new tracks for all detections
            for pos in current_positions:
                self.tracks[self.next_id] = SpermTrack(
                    id=self.next_id,
                    positions=[pos],
                    frame_indices=[self.frame_index],
                    velocities=[]
                )
                self.disappeared[self.next_id] = 0
                self.next_id += 1
            return
            
        # Calculate distance matrix between current positions and existing tracks
        if not current_positions:
            # No detections in current frame, mark all as disappeared
            for track_id in self.tracks:
                self.disappeared[track_id] += 1
            return
            
        # Get last position of each existing track
        existing_positions = []
        track_ids = []
        
        for track_id, track in self.tracks.items():
            existing_positions.append(track.positions[-1])
            track_ids.append(track_id)
        
        # Calculate distance matrix
        distances = np.zeros((len(existing_positions), len(current_positions)))
        
        for i, pos1 in enumerate(existing_positions):
            for j, pos2 in enumerate(current_positions):
                # Euclidean distance between positions
                dist = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                distances[i, j] = dist
        
        # Assign positions to tracks based on minimum distance
        used_positions = set()
        for i, track_id in enumerate(track_ids):
            if np.min(distances[i, :]) <= self.max_distance:
                # Find closest position
                j = np.argmin(distances[i, :])
                
                # Check if position already used
                if j in used_positions:
                    # Position already assigned to another track
                    self.disappeared[track_id] += 1
                    continue
                    
                # Update track with new position
                pos = current_positions[j]
                track = self.tracks[track_id]
                
                # Calculate velocity
                prev_pos = track.positions[-1]
                dx = pos[0] - prev_pos[0]
                dy = pos[1] - prev_pos[1]
                distance = math.sqrt(dx**2 + dy**2)
                
                if len(track.frame_indices) > 0:
                    frames_passed = self.frame_index - track.frame_indices[-1]
                    if frames_passed > 0:
                        velocity = distance / frames_passed
                        track.velocities.append(velocity)
                
                # Update track
                track.positions.append(pos)
                track.frame_indices.append(self.frame_index)
                self.disappeared[track_id] = 0
                
                # Mark position as used
                used_positions.add(j)
            else:
                # No matching position, mark as disappeared
                self.disappeared[track_id] += 1
        
        # Create new tracks for unused detections
        for j, pos in enumerate(current_positions):
            if j not in used_positions:
                self.tracks[self.next_id] = SpermTrack(
                    id=self.next_id,
                    positions=[pos],
                    frame_indices=[self.frame_index],
                    velocities=[]
                )
                self.disappeared[self.next_id] = 0
                self.next_id += 1
    
    def _handle_disappeared(self):
        """
        Handle disappearance of tracks
        
        Returns:
            list: List of completed SpermTrack objects
        """
        completed = []
        ids_to_remove = []
        
        for track_id, count in self.disappeared.items():
            if count > self.max_disappeared:
                # Track lost for too many frames, consider it completed
                completed.append(self.tracks[track_id])
                ids_to_remove.append(track_id)
        
        # Remove completed tracks
        for track_id in ids_to_remove:
            del self.tracks[track_id]
            del self.disappeared[track_id]
        
        return completed
    
    def _draw_tracks(self, frame):
        """
        Draw tracks on frame for visualization
        
        Args:
            frame (numpy.ndarray): Frame to draw on
        """
        for track_id, track in self.tracks.items():
            # Draw track path
            positions = track.positions
            
            if len(positions) > 1:
                # Draw trail (last 20 positions)
                trail_length = min(20, len(positions))
                for i in range(1, trail_length):
                    p1 = positions[-i]
                    p2 = positions[-(i+1)]
                    # Fade color based on position in trail
                    alpha = 1.0 - (i / trail_length)
                    color = (0, int(255 * alpha), int(255 * (1 - alpha)))
                    cv2.line(frame, p1, p2, color, 1)
            
            # Draw current position
            if positions:
                cv2.circle(frame, positions[-1], 3, (0, 0, 255), -1)
                
                # Display ID
                cv2.putText(
                    frame, 
                    f"#{track_id}", 
                    (positions[-1][0] + 5, positions[-1][1] - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.4, 
                    (0, 255, 0), 
                    1
                ) 