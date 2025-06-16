"""
Visualization module for the Automated Sperm Analysis System
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import logging
import datetime

class Visualizer:
    """
    Generate visualizations and reports from sperm analysis data
    """
    
    def __init__(self, output_dir="output"):
        """Initialize visualizer"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.logger = logging.getLogger(__name__)
        
    def plot_trajectories(self, tracks, max_tracks=None):
        """Plot sperm trajectories"""
        plt.figure(figsize=(12, 10))
        
        if not tracks:
            plt.text(0.5, 0.5, "No tracks available", ha='center')
            plt.title("Sperm Trajectories")
            output_path = self.output_dir / "trajectories.png"
            plt.savefig(output_path)
            return str(output_path)
        
        # Limit number of tracks if needed
        plot_tracks = tracks
        if max_tracks and len(tracks) > max_tracks:
            plot_tracks = tracks[:max_tracks]
            
        # Get color map for trajectories
        colors = plt.cm.jet(np.linspace(0, 1, len(plot_tracks)))
        
        # Plot each track
        for i, track in enumerate(plot_tracks):
            positions = np.array(track.positions)
            if len(positions) > 1:
                plt.plot(positions[:, 0], positions[:, 1], color=colors[i], alpha=0.7)
                plt.scatter(positions[0, 0], positions[0, 1], color=colors[i], s=30, marker='o')
                plt.scatter(positions[-1, 0], positions[-1, 1], color=colors[i], s=50, marker='*')
        
        plt.title(f"Sperm Trajectories (n={len(tracks)})")
        plt.xlabel("X position (pixels)")
        plt.ylabel("Y position (pixels)")
        
        output_path = self.output_dir / "trajectories.png"
        plt.savefig(output_path)
        plt.close()
        
        return str(output_path)
    
    def plot_velocity_distribution(self, results):
        """Plot velocity distribution histogram"""
        if results.track_data.empty:
            plt.figure(figsize=(10, 6))
            plt.title("No velocity data available")
            output_path = self.output_dir / "velocity_distribution.png"
            plt.savefig(output_path)
            return str(output_path)
        
        # Create figure with 3 subplots
        fig, ax = plt.subplots(1, 3, figsize=(15, 5))
        
        # Plot VCL (curvilinear velocity)
        vcl_data = results.track_data['vcl'].dropna()
        if not vcl_data.empty:
            ax[0].hist(vcl_data, bins=20, color='blue', alpha=0.7)
            ax[0].set_title('Curvilinear Velocity (VCL)')
            ax[0].set_xlabel('Velocity (μm/s)')
            
        # Plot VSL (straight-line velocity)
        vsl_data = results.track_data['vsl'].dropna()
        if not vsl_data.empty:
            ax[1].hist(vsl_data, bins=20, color='green', alpha=0.7)
            ax[1].set_title('Straight-line Velocity (VSL)')
            
        # Plot linearity
        lin_data = results.track_data['lin'].dropna()
        if not lin_data.empty:
            ax[2].hist(lin_data, bins=20, color='red', alpha=0.7)
            ax[2].set_title('Linearity (LIN)')
        
        plt.tight_layout()
        
        output_path = self.output_dir / "velocity_distribution.png"
        plt.savefig(output_path)
        plt.close()
        
        return str(output_path)
    
    def generate_report(self, results):
        """Generate HTML report with analysis results"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CASA-Lite: Sperm Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background-color: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
                .results table {{ border-collapse: collapse; width: 100%; }}
                .results th, .results td {{ border: 1px solid #ddd; padding: 8px; }}
                .figures {{ display: flex; flex-wrap: wrap; }}
                .figure {{ margin-bottom: 20px; text-align: center; width: 100%; }}
                .figure img {{ max-width: 100%; height: auto; }}
                .footer {{ margin-top: 30px; text-align: center; font-size: 0.8em; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>CASA-Lite: Sperm Analysis Report</h1>
                    <p>Generated on: {timestamp}</p>
                </div>
                
                <div class="results">
                    <h2>Motility Analysis Results</h2>
                    <table>
                        <tr><th>Parameter</th><th>Value</th></tr>
                        <tr><td>Total sperm count</td><td>{results.total_count}</td></tr>
                        <tr><td>Motile sperm</td><td>{results.motile_count} ({results.motility_percent:.1f}%)</td></tr>
                        <tr><td>Immotile sperm</td><td>{results.immotile_count}</td></tr>
                        <tr><td>Curvilinear velocity (VCL)</td><td>{results.vcl:.2f} μm/s</td></tr>
                        <tr><td>Straight-line velocity (VSL)</td><td>{results.vsl:.2f} μm/s</td></tr>
                        <tr><td>Average path velocity (VAP)</td><td>{results.vap:.2f} μm/s</td></tr>
                        <tr><td>Linearity (LIN)</td><td>{results.lin:.2f}</td></tr>
                        <tr><td>Wobble (WOB)</td><td>{results.wobble:.2f}</td></tr>
                        <tr><td>Progression (PROG)</td><td>{results.progression:.2f}</td></tr>
                        <tr><td>Beat-cross frequency (BCF)</td><td>{results.bcf:.2f} Hz</td></tr>
                    </table>
                </div>
                
                <div class="figures">
                    <div class="figure">
                        <h3>Sperm Trajectories</h3>
                        <img src="trajectories.png" alt="Sperm Trajectories">
                    </div>
                    
                    <div class="figure">
                        <h3>Velocity Distributions</h3>
                        <img src="velocity_distribution.png" alt="Velocity Distributions">
                    </div>
                </div>
                
                <div class="footer">
                    <p>CASA-Lite: An affordable Computer-Assisted Sperm Analysis Tool</p>
                    <p>Developed by Saheed Kolawole</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        output_path = self.output_dir / "report.html"
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        return str(output_path) 