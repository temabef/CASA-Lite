"""
Analysis module for the Automated Sperm Analysis System
"""

import numpy as np
import pandas as pd
import math
import logging
from dataclasses import dataclass
from typing import List, Dict, Any
from collections import defaultdict

@dataclass
class MotilityResults:
    """Class for storing sperm motility analysis results"""
    total_count: int
    motile_count: int
    immotile_count: int
    motility_percent: float
    vcl: float  # Curvilinear velocity (μm/s)
    vsl: float  # Straight line velocity (μm/s)
    vap: float  # Average path velocity (μm/s)
    lin: float  # Linearity (VSL/VCL)
    wobble: float  # Wobble (VAP/VCL)
    progression: float  # Progression (VSL/VAP)
    bcf: float  # Beat-cross frequency (Hz)
    track_data: pd.DataFrame
    
    @property
    def summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            "total_count": self.total_count,
            "motile_count": self.motile_count,
            "immotile_count": self.immotile_count,
            "motility_percent": self.motility_percent,
            "vcl": self.vcl,
            "vsl": self.vsl,
            "vap": self.vap,
            "lin": self.lin,
            "wobble": self.wobble,
            "progression": self.progression,
            "bcf": self.bcf
        }


class MotilityAnalyzer:
    """
    Analyzes sperm motility from tracking data
    """
    
    def __init__(self, min_track_length=10, pixels_per_micron=1.0, fps=30.0):
        """
        Initialize motility analyzer
        
        Args:
            min_track_length (int): Minimum length of track to be analyzed
            pixels_per_micron (float): Conversion factor from pixels to microns
            fps (float): Frames per second of the video
        """
        self.min_track_length = min_track_length
        self.pixels_per_micron = pixels_per_micron
        self.fps = fps
        self.logger = logging.getLogger(__name__)
    
    def analyze(self, tracks):
        """
        Analyze motility parameters for tracked sperm cells
        
        Args:
            tracks (list): List of SpermTrack objects
            
        Returns:
            MotilityResults: Analysis results
        """
        # Filter tracks that are too short
        valid_tracks = [t for t in tracks if len(t.positions) >= self.min_track_length]
        
        if not valid_tracks:
            self.logger.warning("No valid tracks found for analysis")
            return self._create_empty_results()
        
        # Extract track data into DataFrame
        track_data = self._extract_track_data(valid_tracks)
        
        # Calculate motility statistics
        total_count = len(tracks)
        motile_count = len([t for t in valid_tracks if self._is_motile(t)])
        immotile_count = total_count - motile_count
        motility_percent = (motile_count / total_count * 100) if total_count > 0 else 0
        
        # Calculate velocity parameters
        vcl = track_data['vcl'].mean()  # Curvilinear velocity
        vsl = track_data['vsl'].mean()  # Straight-line velocity
        vap = track_data['vap'].mean()  # Average path velocity
        
        # Calculate motion characteristics
        lin = track_data['lin'].mean()  # Linearity
        wobble = vap / vcl if vcl > 0 else 0  # Wobble
        progression = vsl / vap if vap > 0 else 0  # Progression
        
        # Calculate beat frequency
        bcf = self._calculate_bcf(valid_tracks)
        
        self.logger.info(f"Analysis complete: {motile_count}/{total_count} motile ({motility_percent:.1f}%)")
        
        return MotilityResults(
            total_count=total_count,
            motile_count=motile_count,
            immotile_count=immotile_count,
            motility_percent=motility_percent,
            vcl=vcl,
            vsl=vsl,
            vap=vap,
            lin=lin,
            wobble=wobble,
            progression=progression,
            bcf=bcf,
            track_data=track_data
        )
    
    def _extract_track_data(self, tracks):
        """
        Extract track data into a DataFrame
        
        Args:
            tracks (list): List of tracks
            
        Returns:
            pd.DataFrame: Track data
        """
        data = []
        
        for track in tracks:
            # Calculate velocities
            total_distance = track.total_distance * self.pixels_per_micron
            straight_distance = track.straight_line_distance * self.pixels_per_micron
            
            # Calculate time elapsed in seconds
            if len(track.frame_indices) >= 2:
                time_elapsed = (track.frame_indices[-1] - track.frame_indices[0]) / self.fps
            else:
                time_elapsed = 1 / self.fps
                
            # Avoid division by zero
            if time_elapsed > 0:
                vcl = total_distance / time_elapsed  # μm/s
                vsl = straight_distance / time_elapsed  # μm/s
            else:
                vcl = vsl = 0
                
            # Average path velocity (simplified)
            vap = track.avg_velocity * self.pixels_per_micron * self.fps  # μm/s
            
            # Calculate linearity
            lin = track.linearity
            
            # Add to data list
            data.append({
                'track_id': track.id,
                'length': len(track.positions),
                'duration': time_elapsed,
                'total_distance': total_distance,
                'straight_distance': straight_distance,
                'vcl': vcl,
                'vsl': vsl,
                'vap': vap,
                'lin': lin,
                'is_motile': self._is_motile(track)
            })
        
        return pd.DataFrame(data)
    
    def _is_motile(self, track, threshold=10.0):
        """
        Determine if a track represents a motile sperm
        
        Args:
            track: SpermTrack object
            threshold (float): Minimum distance (in pixels) to be considered motile
            
        Returns:
            bool: True if motile, False otherwise
        """
        # Simple criterion: if the sperm moved more than threshold pixels,
        # it's considered motile
        return track.total_distance > threshold
    
    def _calculate_bcf(self, tracks):
        """
        Calculate beat-cross frequency (BCF)
        
        Args:
            tracks (list): List of track objects
            
        Returns:
            float: Average BCF in Hz
        """
        beat_frequencies = []
        
        for track in tracks:
            # Count the number of times the sperm crosses its average path
            # This is simplified - in a real implementation, we would need to calculate
            # the average path and count crossings
            if len(track.positions) < 3:
                continue
                
            # Simplified BCF: count direction changes as an approximation
            direction_changes = 0
            prev_dx = prev_dy = 0
            
            for i in range(1, len(track.positions)):
                x1, y1 = track.positions[i-1]
                x2, y2 = track.positions[i]
                
                dx = x2 - x1
                dy = y2 - y1
                
                # Check for direction change in x or y
                if i > 1 and ((dx * prev_dx < 0) or (dy * prev_dy < 0)):
                    direction_changes += 1
                    
                prev_dx = dx
                prev_dy = dy
            
            # Calculate frames elapsed
            frames_elapsed = track.frame_indices[-1] - track.frame_indices[0]
            if frames_elapsed > 0:
                # Convert to Hz (beats per second)
                bcf = direction_changes / (frames_elapsed / self.fps)
                beat_frequencies.append(bcf)
        
        # Calculate average BCF
        if beat_frequencies:
            return sum(beat_frequencies) / len(beat_frequencies)
        else:
            return 0.0
    
    def _create_empty_results(self):
        """Create empty results when no valid tracks are found"""
        return MotilityResults(
            total_count=0,
            motile_count=0,
            immotile_count=0,
            motility_percent=0,
            vcl=0,
            vsl=0,
            vap=0,
            lin=0,
            wobble=0,
            progression=0,
            bcf=0,
            track_data=pd.DataFrame()
        )
    
    def classify_tracks(self, tracks):
        """
        Classify tracks into motility categories
        
        Args:
            tracks (list): List of SpermTrack objects
            
        Returns:
            dict: Counts of each motility category
        """
        categories = {
            'rapid': 0,
            'medium': 0,
            'slow': 0,
            'immotile': 0
        }
        
        for track in tracks:
            if len(track.positions) < self.min_track_length:
                categories['immotile'] += 1
                continue
            
            # Calculate VCL (curvilinear velocity)
            if len(track.frame_indices) >= 2:
                time_elapsed = (track.frame_indices[-1] - track.frame_indices[0]) / self.fps
                if time_elapsed > 0:
                    vcl = (track.total_distance * self.pixels_per_micron) / time_elapsed
                else:
                    vcl = 0
            else:
                vcl = 0
            
            # Classify based on VCL
            if not self._is_motile(track):
                categories['immotile'] += 1
            elif vcl > 100:  # μm/s
                categories['rapid'] += 1
            elif vcl > 50:
                categories['medium'] += 1
            else:
                categories['slow'] += 1
                
        return categories 