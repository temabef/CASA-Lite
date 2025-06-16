"""
Visualization module for the Automated Sperm Analysis System
"""

import os
import numpy as np
import matplotlib
# Use Agg backend (non-interactive) to prevent thread issues
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import logging
import datetime
import base64
import io

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
            plt.savefig(output_path, dpi=150)
            plt.close()
            return str(output_path), self._get_image_base64(output_path)
        
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
        
        # Save to file and get base64
        output_path = self.output_dir / "trajectories.png"
        plt.savefig(output_path, dpi=150)
        plt.close()
        
        return str(output_path), self._get_image_base64(output_path)
    
    def plot_velocity_distribution(self, results):
        """Plot velocity distribution histogram"""
        if results.track_data.empty:
            plt.figure(figsize=(10, 6))
            plt.title("No velocity data available")
            output_path = self.output_dir / "velocity_distribution.png"
            plt.savefig(output_path, dpi=150)
            plt.close()
            return str(output_path), self._get_image_base64(output_path)
        
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
            ax[1].set_xlabel('Velocity (μm/s)')
            
        # Plot linearity
        lin_data = results.track_data['lin'].dropna()
        if not lin_data.empty:
            ax[2].hist(lin_data, bins=20, color='red', alpha=0.7)
            ax[2].set_title('Linearity (LIN)')
            ax[2].set_xlabel('Linearity Index')
        
        plt.tight_layout()
        
        # Save to file and get base64
        output_path = self.output_dir / "velocity_distribution.png"
        plt.savefig(output_path, dpi=150)
        plt.close()
        
        return str(output_path), self._get_image_base64(output_path)
    
    def _get_image_base64(self, image_path):
        """Convert image to base64 string"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error encoding image to base64: {e}")
            return ""
    
    def generate_report(self, results, tracks=None):
        """Generate HTML report with analysis results"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get logo as base64
        logo_path = Path(__file__).parent.parent / "static" / "images" / "logo.svg"
        logo_base64 = ""
        if logo_path.exists():
            try:
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                    logo_base64 = base64.b64encode(logo_data).decode('utf-8')
            except Exception as e:
                self.logger.error(f"Error loading logo: {e}")
        
        # Generate plots and get base64 encoded images
        # Use provided tracks or empty list if none provided
        trajectories_path, trajectories_base64 = self.plot_trajectories(tracks if tracks is not None else [])
        velocity_path, velocity_base64 = self.plot_velocity_distribution(results)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CASA-Lite: Sperm Analysis Report</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                :root {{
                    --primary-color: #2c3e50;
                    --secondary-color: #3498db;
                    --accent-color: #2ecc71;
                    --light-bg: #f8f9fa;
                    --dark-bg: #343a40;
                    --text-color: #333;
                    --light-text: #f8f9fa;
                    --border-radius: 8px;
                    --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0; 
                    padding: 0; 
                    background-color: var(--light-bg);
                    color: var(--text-color);
                    line-height: 1.6;
                }}
                
                .container {{ 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    padding: 20px; 
                }}
                
                header {{
                    background-color: var(--primary-color);
                    color: white;
                    padding: 1rem 0;
                    margin-bottom: 2rem;
                    box-shadow: var(--box-shadow);
                }}
                
                .header-content {{
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 0 2rem;
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                
                .logo {{
                    display: flex;
                    align-items: center;
                }}
                
                .logo img {{
                    height: 60px;
                    margin-right: 15px;
                    filter: drop-shadow(0px 0px 3px rgba(255, 255, 255, 0.3));
                }}
                
                h1, h2, h3 {{ 
                    color: var(--primary-color);
                    margin-bottom: 1rem;
                }}
                
                h1 {{
                    font-size: 2.5rem;
                    text-align: center;
                    margin-top: 0;
                }}
                
                .results {{ 
                    background: white;
                    padding: 2rem;
                    border-radius: var(--border-radius);
                    box-shadow: var(--box-shadow);
                    margin-top: 2rem;
                }}
                
                .results table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                }}
                
                .results th, .results td {{ 
                    border: 1px solid #ddd; 
                    padding: 12px; 
                    text-align: left;
                }}
                
                .results th {{ 
                    background-color: var(--light-bg);
                }}
                
                .results tr:nth-child(even) {{ 
                    background-color: #f2f2f2;
                }}
                
                .figures {{ 
                    display: flex; 
                    flex-wrap: wrap; 
                    gap: 20px;
                    margin-top: 30px;
                }}
                
                .figure {{ 
                    flex: 1 1 100%;
                    margin-bottom: 20px; 
                    text-align: center; 
                    background: white;
                    border-radius: var(--border-radius);
                    padding: 1rem;
                    box-shadow: var(--box-shadow);
                }}
                
                .figure img {{ 
                    max-width: 100%; 
                    height: auto; 
                    border-radius: var(--border-radius);
                }}
                
                .footer {{ 
                    margin-top: 30px; 
                    text-align: center; 
                    font-size: 0.8em; 
                    color: #777; 
                    padding: 1.5rem 0;
                    border-top: 1px solid #eee;
                }}
                
                @media (min-width: 768px) {{
                    .figure {{ 
                        flex: 0 0 calc(50% - 10px);
                    }}
                }}
            </style>
        </head>
        <body>
            <header>
                <div class="header-content">
                    <div class="logo">
                        {"<img src='data:image/svg+xml;base64," + logo_base64 + "' alt='CASA-Lite Logo'>" if logo_base64 else "CASA-Lite"}
                    </div>
                </div>
            </header>
            
            <div class="container">
                <h1>Sperm Analysis Report</h1>
                <p style="text-align: center;">Generated on: {timestamp}</p>
                
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
                        <img src="data:image/png;base64,{trajectories_base64}" alt="Sperm Trajectories">
                        <p>Visualization of sperm movement paths tracked during analysis</p>
                    </div>
                    
                    <div class="figure">
                        <h3>Velocity Distributions</h3>
                        <img src="data:image/png;base64,{velocity_base64}" alt="Velocity Distributions">
                        <p>Distribution of velocity parameters across all tracked sperm cells</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>CASA-Lite: An affordable Computer-Assisted Sperm Analysis Tool</p>
                    <p>Developed by Saheed Kolawole</p>
                    <p><a href="https://github.com/temabef/CASA-Lite" target="_blank">GitHub Repository</a> | <a href="https://temabef.github.io/CASA-Lite/" target="_blank">Documentation</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        output_path = self.output_dir / "report.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path) 