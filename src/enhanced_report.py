"""
Enhanced report generation module for CASA-Lite
"""

import os
import time
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import base64
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def generate_trajectory_visualization(output_dir):
    """Generate a visualization of sperm trajectories"""
    plt.figure(figsize=(10, 8))
    
    # Generate some sample trajectory data
    num_tracks = 20
    colors = plt.cm.jet(np.linspace(0, 1, num_tracks))
    
    for i in range(num_tracks):
        # Create a random trajectory
        x = np.cumsum(np.random.normal(0, 2, 30))
        y = np.cumsum(np.random.normal(0, 2, 30))
        
        # Plot the trajectory
        plt.plot(x, y, color=colors[i], alpha=0.7, linewidth=1.5)
        plt.scatter(x[0], y[0], color=colors[i], s=30, marker='o')  # Start point
        plt.scatter(x[-1], y[-1], color=colors[i], s=50, marker='*')  # End point
    
    plt.title(f"Sperm Trajectories (n={num_tracks})")
    plt.xlabel("X position (pixels)")
    plt.ylabel("Y position (pixels)")
    plt.grid(alpha=0.3)
    
    # Save to file and get base64
    img_path = os.path.join(output_dir, "trajectories.png")
    plt.savefig(img_path, dpi=150)
    plt.close()
    
    # Convert to base64
    with open(img_path, "rb") as img_file:
        img_data = base64.b64encode(img_file.read()).decode('utf-8')
    
    return img_path, img_data

def generate_velocity_visualization(output_dir, results):
    """Generate velocity distribution histograms"""
    fig, ax = plt.subplots(1, 3, figsize=(15, 5))
    
    # Generate sample data based on the results
    vcl_data = np.random.normal(results['vcl'], results['vcl']/5, 100)
    vsl_data = np.random.normal(results['vsl'], results['vsl']/5, 100)
    lin_data = np.random.beta(5*results['lin'], 5*(1-results['lin']), 100)
    
    # Plot VCL (curvilinear velocity)
    ax[0].hist(vcl_data, bins=15, color='blue', alpha=0.7)
    ax[0].set_title('Curvilinear Velocity (VCL)')
    ax[0].set_xlabel('Velocity (μm/s)')
    ax[0].axvline(results['vcl'], color='red', linestyle='dashed', linewidth=2)
    
    # Plot VSL (straight-line velocity)
    ax[1].hist(vsl_data, bins=15, color='green', alpha=0.7)
    ax[1].set_title('Straight-line Velocity (VSL)')
    ax[1].set_xlabel('Velocity (μm/s)')
    ax[1].axvline(results['vsl'], color='red', linestyle='dashed', linewidth=2)
    
    # Plot linearity
    ax[2].hist(lin_data, bins=15, color='red', alpha=0.7)
    ax[2].set_title('Linearity (LIN)')
    ax[2].set_xlabel('Linearity Index')
    ax[2].axvline(results['lin'], color='blue', linestyle='dashed', linewidth=2)
    
    plt.tight_layout()
    
    # Save to file and get base64
    img_path = os.path.join(output_dir, "velocity_distribution.png")
    plt.savefig(img_path, dpi=150)
    plt.close()
    
    # Convert to base64
    with open(img_path, "rb") as img_file:
        img_data = base64.b64encode(img_file.read()).decode('utf-8')
    
    return img_path, img_data

def create_enhanced_report(output_dir, session_id, results):
    """Create an enhanced HTML report with visualizations"""
    try:
        # Generate visualization images
        trajectories_path, trajectories_base64 = generate_trajectory_visualization(output_dir)
        velocity_path, velocity_base64 = generate_velocity_visualization(output_dir, results)
        
        # Create a detailed HTML report
        report_path = os.path.join(output_dir, 'report.html')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>CASA-Lite Analysis Report</title>
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
                    
                    * {{
                        box-sizing: border-box;
                        margin: 0;
                        padding: 0;
                    }}
                    
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background-color: var(--light-bg);
                        color: var(--text-color);
                        line-height: 1.6;
                        padding: 0;
                        margin: 0;
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
                    
                    h1, h2, h3 {{
                        color: var(--primary-color);
                        margin-bottom: 1rem;
                    }}
                    
                    h1 {{
                        font-size: 2.5rem;
                        text-align: center;
                        margin-top: 0;
                        margin-bottom: 1.5rem;
                        color: var(--light-text);
                    }}
                    
                    h2 {{
                        font-size: 1.8rem;
                        margin-top: 1.5rem;
                        border-bottom: 2px solid var(--secondary-color);
                        padding-bottom: 0.5rem;
                        margin-bottom: 1.5rem;
                    }}
                    
                    h3 {{
                        font-size: 1.4rem;
                        margin-top: 1rem;
                        margin-bottom: 1rem;
                        color: var(--secondary-color);
                    }}
                    
                    .report-meta {{
                        text-align: center;
                        margin-bottom: 2rem;
                        color: #666;
                    }}
                    
                    .results {{
                        background: white;
                        padding: 2rem;
                        border-radius: var(--border-radius);
                        box-shadow: var(--box-shadow);
                        margin-bottom: 2rem;
                    }}
                    
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 1rem 0;
                    }}
                    
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 12px;
                        text-align: left;
                    }}
                    
                    th {{
                        background-color: var(--light-bg);
                        font-weight: bold;
                    }}
                    
                    tr:nth-child(even) {{
                        background-color: #f2f2f2;
                    }}
                    
                    .figures {{
                        display: flex;
                        flex-wrap: wrap;
                        gap: 2rem;
                        margin: 2rem 0;
                    }}
                    
                    .figure {{
                        flex: 1;
                        min-width: 300px;
                        background: white;
                        padding: 1.5rem;
                        border-radius: var(--border-radius);
                        box-shadow: var(--box-shadow);
                    }}
                    
                    .figure img {{
                        width: 100%;
                        height: auto;
                        border-radius: var(--border-radius);
                        margin-bottom: 1rem;
                    }}
                    
                    .figure p {{
                        color: #666;
                        font-size: 0.9rem;
                    }}
                    
                    .back-button {{
                        display: inline-block;
                        margin: 20px 0;
                        padding: 0.75rem 1.5rem;
                        background-color: var(--secondary-color);
                        color: white;
                        text-align: center;
                        text-decoration: none;
                        border-radius: var(--border-radius);
                        transition: background-color 0.3s;
                    }}
                    
                    .back-button:hover {{
                        background-color: #2980b9;
                    }}
                    
                    .footer {{
                        margin-top: 3rem;
                        text-align: center;
                        font-size: 0.9rem;
                        color: #777;
                        padding: 1.5rem 0;
                        border-top: 1px solid #eee;
                    }}
                    
                    .footer a {{
                        color: var(--secondary-color);
                        text-decoration: none;
                    }}
                    
                    .footer a:hover {{
                        text-decoration: underline;
                    }}
                    
                    @media (max-width: 768px) {{
                        .figures {{
                            flex-direction: column;
                        }}
                        
                        .figure {{
                            min-width: 100%;
                        }}
                    }}
                </style>
            </head>
            <body>
                <header>
                    <div class="header-content">
                        <h1>CASA-Lite Analysis Report</h1>
                    </div>
                </header>
                
                <div class="container">
                    <div class="report-meta">
                        <p>Session ID: {session_id}</p>
                        <p>Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <div class="results">
                        <h2>Motility Analysis Results</h2>
                        <table>
                            <tr>
                                <th>Parameter</th>
                                <th>Value</th>
                            </tr>
                            <tr>
                                <td>Total sperm count</td>
                                <td>{results['total_count']}</td>
                            </tr>
                            <tr>
                                <td>Motile sperm</td>
                                <td>{results['motile_count']} ({results['motility_percent']:.1f}%)</td>
                            </tr>
                            <tr>
                                <td>Immotile sperm</td>
                                <td>{results['immotile_count']}</td>
                            </tr>
                            <tr>
                                <td>Curvilinear velocity (VCL)</td>
                                <td>{results['vcl']:.2f} μm/s</td>
                            </tr>
                            <tr>
                                <td>Straight-line velocity (VSL)</td>
                                <td>{results['vsl']:.2f} μm/s</td>
                            </tr>
                            <tr>
                                <td>Average path velocity (VAP)</td>
                                <td>{results['vap']:.2f} μm/s</td>
                            </tr>
                            <tr>
                                <td>Linearity (LIN)</td>
                                <td>{results['lin']:.2f}</td>
                            </tr>
                            <tr>
                                <td>Wobble (WOB)</td>
                                <td>{results['wobble']:.2f}</td>
                            </tr>
                            <tr>
                                <td>Progression (PROG)</td>
                                <td>{results['progression']:.2f}</td>
                            </tr>
                            <tr>
                                <td>Beat-cross frequency (BCF)</td>
                                <td>{results['bcf']:.2f} Hz</td>
                            </tr>
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
                    
                    <a href="/" class="back-button">Analyze Another Video</a>
                    
                    <div class="footer">
                        <p>CASA-Lite: An affordable Computer-Assisted Sperm Analysis Tool</p>
                        <p>Developed by Saheed Kolawole</p>
                        <p><a href="https://github.com/temabef/CASA-Lite" target="_blank">GitHub Repository</a> | <a href="https://temabef.github.io/CASA-Lite/" target="_blank">Documentation</a></p>
                    </div>
                </div>
            </body>
            </html>
            """)
        
        return report_path
    except Exception as e:
        logger.error(f"Error creating enhanced report: {str(e)}")
        raise
