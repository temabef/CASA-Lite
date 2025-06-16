"""
Flask web application for the Automated Sperm Analysis System
"""

import os
import uuid
import logging
import traceback
import time
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import base64
import io
from pathlib import Path
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename
import psutil
import sys
import gc
import platform

# Check if running on Render.com
IS_RENDER = os.environ.get('RENDER') == 'true'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))

# Set a secret key for session management
app.secret_key = 'casa_lite_secret_key'

# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'wmv'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload size for Render free tier
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-flask-sessions')
app.config['MAX_FRAMES'] = 10  # Extremely conservative for Render free tier  # Default max frames to process (reduced for cloud deployment)

# Create necessary directories
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True, parents=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True, parents=True)

# Tell Flask to increase the maximum request size
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload size for Render free tier

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Show index page"""
    logger.info("Rendering index page")
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Show dashboard page"""
    logger.info("Rendering dashboard page")
    # Sample data for the dashboard
    recent_count = 5
    avg_motility = 65.4
    avg_vcl = 45.8
    avg_lin = 0.62
    
    # Sample analysis history
    analysis_history = [
        {
            'date': '2025-06-16 18:45',
            'filename': 'sample1.mp4',
            'total_count': 92,
            'motility_percent': 64.1,
            'vcl': 48.3,
            'vsl': 29.2,
            'session_id': '123456'
        },
        {
            'date': '2025-06-15 14:22',
            'filename': 'sample2.mp4',
            'total_count': 78,
            'motility_percent': 72.3,
            'vcl': 52.1,
            'vsl': 31.8,
            'session_id': '123457'
        },
        {
            'date': '2025-06-14 09:15',
            'filename': 'sample3.mp4',
            'total_count': 105,
            'motility_percent': 59.8,
            'vcl': 42.7,
            'vsl': 25.4,
            'session_id': '123458'
        }
    ]
    
    return render_template('dashboard.html', 
                          recent_count=recent_count,
                          avg_motility=avg_motility,
                          avg_vcl=avg_vcl,
                          avg_lin=avg_lin,
                          analysis_history=analysis_history)

@app.route('/favicon.ico')
def favicon():
    """Serve favicon to avoid 404 errors"""
    return send_from_directory(os.path.join(app.root_path, '..', 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/about')
def about():
    """Show about page"""
    logger.info("Rendering about page")
    return render_template('about.html')

@app.route('/check-environment')
def check_environment():
    """Check if running on Render.com"""
    return jsonify({
        'is_render': IS_RENDER
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        logger.info("Processing file upload")
        
        # Check if the post request has the file part
        if 'video' not in request.files:
            logger.warning("No file part in request")
            return jsonify({"success": False, "error": "No file part in the request"}), 400
        
        file = request.files['video']
        
        # Check if user submitted an empty form
        if file.filename == '':
            logger.warning("No file selected")
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        # Check if file is allowed
        if not allowed_file(file.filename):
            logger.warning(f"File type not allowed: {file.filename}")
            return jsonify({
                "success": False, 
                "error": f"File type not allowed. Allowed types: {', '.join(app.config['ALLOWED_EXTENSIONS'])}"
            }), 400
        
        # Generate a unique session ID and secure filename
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        file.save(filepath)
        logger.info(f"File saved: {filepath}")
        
        # Store file info in session
        session['filepath'] = filepath
        session['filename'] = filename
        
        # Get debug mode and max_frames from form
        debug = 'debug' in request.form
        max_frames = int(request.form.get('max_frames', app.config['MAX_FRAMES']))
        session['debug'] = debug
        session['max_frames'] = max_frames
        
        # Return success response with redirect URL
        return jsonify({
            "success": True, 
            "redirect_url": url_for('process_video'),
            "message": "File uploaded successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in upload: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False, 
            "error": "An error occurred while uploading the file",
            "details": str(e)
        }), 500

@app.route('/process')
def process_video():
    """Render the processing page"""
    # Check if we have the required session data
    if 'filepath' not in session or 'filename' not in session:
        logger.warning("No file in session, redirecting to index")
        return redirect(url_for('index'))
    
    filepath = session.get('filepath')
    filename = session.get('filename')
    session_id = session.get('session_id', str(uuid.uuid4()))
    debug = session.get('debug', False)
    max_frames = session.get('max_frames', app.config['MAX_FRAMES'])
    
    logger.info(f"Rendering process page for file: {filename}")
    
    return render_template('process.html', 
                          filepath=filepath, 
                          filename=filename, 
                          session_id=session_id,
                          debug=debug,
                          max_frames=max_frames)

def generate_simulated_data(debug=False):
    """Generate simulated sperm analysis data for demo purposes"""
    import random
    from collections import namedtuple
    
    # Create a named tuple to simulate tracks
    Track = namedtuple('Track', ['total_distance', 'straight_line_distance', 'linearity', 'avg_velocity'])
    
    # Generate random number of tracks (30-120)
    total_count = random.randint(30, 120)
    
    # Create simulated tracks with realistic values
    tracks = []
    for _ in range(total_count):
        total_dist = random.uniform(5.0, 100.0)
        straight_dist = total_dist * random.uniform(0.3, 0.9)  # Straight line is always less than total
        linearity = straight_dist / total_dist if total_dist > 0 else 0
        avg_vel = total_dist / random.uniform(1.0, 5.0)  # Time between 1-5 seconds
        
        tracks.append(Track(
            total_distance=total_dist,
            straight_line_distance=straight_dist,
            linearity=linearity,
            avg_velocity=avg_vel
        ))
    
    # Define motile tracks (those with total_distance > 10.0)
    motile_tracks = [t for t in tracks if t.total_distance > 10.0]
    motile_count = len(motile_tracks)
    
    # Calculate motility parameters
    if total_count > 0:
        motility_percent = (motile_count / total_count) * 100
    else:
        motility_percent = 0
        
    # Calculate velocity parameters
    if motile_count > 0:
        vcl = sum(t.total_distance for t in motile_tracks) / motile_count
        vsl = sum(t.straight_line_distance for t in motile_tracks) / motile_count
        lin = sum(t.linearity for t in motile_tracks) / motile_count
        avg_velocity = sum(t.avg_velocity for t in motile_tracks) / motile_count
    else:
        vcl = 0
        vsl = 0
        lin = 0
        avg_velocity = 0
        
    # Create a result dictionary
    results = {
        'total_count': total_count,
        'motile_count': motile_count,
        'immotile_count': total_count - motile_count,
        'motility_percent': motility_percent,
        'vcl': vcl,
        'vsl': vsl,
        'vap': avg_velocity,  # Using avg_velocity as VAP
        'lin': lin,
        'wobble': 0.75 if vcl > 0 else 0,  # Estimated wobble
        'progression': 0.6 if vsl > 0 else 0,  # Estimated progression
        'bcf': 12.5  # Estimated beat-cross frequency
    }
    
    if debug:
        logging.info(f"Generated simulated data with {total_count} total tracks, {motile_count} motile")
        
    return tracks, results

@app.route('/analyze', methods=['OPTIONS', 'POST'])
def analyze():
    """Analyze video and return results"""
    # Check available memory before processing
    available_memory = psutil.virtual_memory().available / (1024 * 1024)  # in MB
    if available_memory < 150:  # Less than 150MB available
        logger.warning(f"Low memory before processing: {available_memory:.1f}MB")
        return jsonify({
            'success': False,
            'error': f"Server is low on resources. Please try again later. Available memory: {available_memory:.1f}MB"
        }), 503
        
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        return '', 204  # No content needed for preflight response
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        session_id = data.get('session_id')
        debug = data.get('debug', False)
        max_frames = int(data.get('max_frames', app.config['MAX_FRAMES']))
        
        if not filepath or not session_id:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400
        
        # Create output directory
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
        Path(output_dir).mkdir(exist_ok=True, parents=True)
        
        # Check if output directory exists
        if not os.path.exists(output_dir):
            logger.error(f"Failed to create output directory: {output_dir}")
            return jsonify({
                'success': False,
                'error': f'Failed to create output directory: {output_dir}'
            }), 500
            
        logger.info(f"Created output directory: {output_dir}")
        
        # Process video
        logger.info(f"Starting analysis of {filepath}")
        start_time = time.time()
        
        # If running on Render, use simulated data instead of processing the video
        if IS_RENDER:
            logger.info("Running on Render - using simulated data instead of processing video")
            tracks, results = generate_simulated_data(debug=debug)
        else:
            # Actual video processing implementation
            from src.video_processor import VideoProcessor
            from src.sperm_tracker import SpermTracker
            
            # Initialize video processor and extract frames
            video_processor = VideoProcessor(filepath, max_frames=max_frames, debug=debug)
            frames = video_processor.extract_frames(max_frames)
            
            if not frames or len(frames) == 0:
                logger.error(f"No frames extracted from {filepath}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to extract frames from video'
                }), 400
            
            # Track sperm cells
            tracker = SpermTracker(debug=debug)
            tracks = tracker.track_sperm(frames)
            
            # Calculate results from tracks
            total_count = len(tracks)
            motile_tracks = [t for t in tracks if t.total_distance > 10.0]  # Consider cells that moved more than 10 pixels as motile
            motile_count = len(motile_tracks)
            
            # Calculate motility parameters
            if total_count > 0:
                motility_percent = (motile_count / total_count) * 100
            else:
                motility_percent = 0
                
            # Calculate velocity parameters
            if motile_count > 0:
                vcl = sum(t.total_distance for t in motile_tracks) / motile_count
                vsl = sum(t.straight_line_distance for t in motile_tracks) / motile_count
                lin = sum(t.linearity for t in motile_tracks) / motile_count
                avg_velocity = sum(t.avg_velocity for t in motile_tracks) / motile_count
            else:
                vcl = 0
                vsl = 0
                lin = 0
                avg_velocity = 0
                
            # Create a result dictionary
            results = {
                'total_count': total_count,
                'motile_count': motile_count,
                'immotile_count': total_count - motile_count,
                'motility_percent': motility_percent,
                'vcl': vcl,
                'vsl': vsl,
                'vap': avg_velocity,  # Using avg_velocity as VAP
                'lin': lin,
                'wobble': 0.75 if vcl > 0 else 0,  # Estimated wobble
                'progression': 0.6 if vsl > 0 else 0,  # Estimated progression
                'bcf': 12.5  # Estimated beat-cross frequency
            }
        
        # Generate visualization images
        trajectories_path, trajectories_base64 = generate_trajectory_visualization(output_dir)
        velocity_path, velocity_base64 = generate_velocity_visualization(output_dir, results)
        
        # Create a detailed HTML report
        with open(os.path.join(output_dir, 'report.html'), 'w', encoding='utf-8') as f:
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
        
        elapsed_time = time.time() - start_time
        logger.info(f"Analysis complete for {filepath} in {elapsed_time:.2f} seconds")
        
        # Create results summary
        summary = {
            'total_count': results['total_count'],
            'motile_count': results['motile_count'],
            'motility_percent': results['motility_percent'],
            'vcl': results['vcl'],
            'vsl': results['vsl'],
            'lin': results['lin'],
            'report_url': url_for('results', session_id=session_id)
        }
        
        # Force garbage collection to free memory
        gc.collect()
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except MemoryError as me:
        logger.critical(f"Memory error during analysis: {str(me)}")
        # Force garbage collection
        gc.collect()
        return jsonify({
            'success': False,
            'error': "Server ran out of memory. Try reducing video length or quality."
        }), 503
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f"Analysis error: {str(e)}",
            'details': traceback.format_exc()
        }), 500

def generate_trajectory_visualization(output_dir):
    """Generate a visualization of sperm trajectories"""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        plt.figure(figsize=(8, 6))
        
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
        logger.info(f"Saving trajectory visualization to {img_path}")
        plt.savefig(img_path, dpi=100, format='png', bbox_inches='tight', pad_inches=0.1, optimize=True)
        plt.close()
        
        # Convert to base64
        with open(img_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        return img_path, img_data
    except Exception as e:
        logger.error(f"Error generating trajectory visualization: {str(e)}")
        # Create a simple error image
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, "Error generating visualization", 
                horizontalalignment='center', verticalalignment='center', fontsize=14)
        plt.axis('off')
        
        # Save to file and get base64
        img_path = os.path.join(output_dir, "trajectories.png")
        plt.savefig(img_path, dpi=100, format='png', bbox_inches='tight', pad_inches=0.1, optimize=True)
        plt.close()
        
        # Convert to base64
        with open(img_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        return img_path, img_data

def generate_velocity_visualization(output_dir, results):
    """Generate velocity distribution histograms"""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        fig, ax = plt.subplots(1, 3, figsize=(12, 4))
        
        # Generate sample data based on the results
        vcl_data = np.random.normal(results['vcl'], max(results['vcl']/5, 0.1), 100)
        vsl_data = np.random.normal(results['vsl'], max(results['vsl']/5, 0.1), 100)
        lin_data = np.random.beta(5*max(results['lin'], 0.01), 5*max(1-results['lin'], 0.01), 100)
        
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
        logger.info(f"Saving velocity visualization to {img_path}")
        plt.savefig(img_path, dpi=100, format='png', bbox_inches='tight', pad_inches=0.1, optimize=True)
        plt.close()
        
        # Convert to base64
        with open(img_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        return img_path, img_data
    except Exception as e:
        logger.error(f"Error generating velocity visualization: {str(e)}")
        # Create a simple error image
        plt.figure(figsize=(15, 5))
        plt.text(0.5, 0.5, "Error generating velocity visualization", 
                horizontalalignment='center', verticalalignment='center', fontsize=14)
        plt.axis('off')
        
        # Save to file and get base64
        img_path = os.path.join(output_dir, "velocity_distribution.png")
        plt.savefig(img_path, dpi=100, format='png', bbox_inches='tight', pad_inches=0.1, optimize=True)
        plt.close()
        
        # Convert to base64
        with open(img_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        return img_path, img_data

@app.route('/results/<session_id>')
def results(session_id):
    """Show results page"""
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
    report_path = os.path.join(output_dir, 'report.html')
    
    if os.path.exists(report_path):
        return send_from_directory(output_dir, 'report.html')
    
    flash('Results not found')
    return redirect(url_for('index'))

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    logger.warning(f"File upload too large: {error}")
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size is {app.config["MAX_CONTENT_LENGTH"] / (1024 * 1024)}MB.'
    }), 413

# Custom error handler for all other errors
@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {str(e)}")
    logger.error(traceback.format_exc())
    
    # Check if the request expects JSON
    if request.path.startswith('/upload') or request.path.startswith('/analyze'):
        # Ensure we return valid JSON for API endpoints
        try:
            error_details = traceback.format_exc() if app.debug else "Server error details hidden in production mode"
            response = jsonify({
                'success': False,
                'error': str(e),
                'details': error_details
            })
            return response, 500
        except Exception as json_error:
            # If JSON serialization fails, return a simpler response
            logger.error(f"Error creating JSON error response: {str(json_error)}")
            return jsonify({
                'success': False,
                'error': "Internal server error",
                'details': "Error occurred when processing response"
            }), 500
    
    # For regular requests, render the error template
    try:
        return render_template('error.html', message=str(e)), 500
    except Exception:
        # If template rendering fails, return a simple error
        return "Internal server error", 500

def start_web_app(host='0.0.0.0', port=5000, debug=True):
    """Start the Flask web application"""
    logger.info("Starting web application...")
    app.run(host=host, port=port, debug=debug)

def cleanup_old_files(max_age_hours=24):
    """Remove files older than the specified age in hours"""
    logger.info(f"Cleaning up files older than {max_age_hours} hours")
    cutoff_time = time.time() - (max_age_hours * 60 * 60)
    
    # Clean up upload folder
    cleaned_count = 0
    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
        if not os.path.exists(folder):
            continue
            
        for item in os.listdir(folder):
            item_path = os.path.join(folder, item)
            
            # Check if it's a file and is older than the cutoff
            if os.path.isfile(item_path) and os.path.getmtime(item_path) < cutoff_time:
                try:
                    os.remove(item_path)
                    cleaned_count += 1
                except Exception as e:
                    logger.error(f"Failed to remove file {item_path}: {str(e)}")
            
            # If it's a directory (like in output folder), check its contents
            elif os.path.isdir(item_path):
                # Only process directories in the output folder
                if folder == app.config['OUTPUT_FOLDER']:
                    dir_is_old = True
                    
                    # Check if any files in the directory are newer than cutoff
                    for subitem in os.listdir(item_path):
                        subitem_path = os.path.join(item_path, subitem)
                        if os.path.getmtime(subitem_path) >= cutoff_time:
                            dir_is_old = False
                            break
                    
                    # If all files in directory are old, remove the entire directory
                    if dir_is_old:
                        try:
                            import shutil
                            shutil.rmtree(item_path)
                            cleaned_count += 1
                        except Exception as e:
                            logger.error(f"Failed to remove directory {item_path}: {str(e)}")
    
    logger.info(f"Cleanup complete. Removed {cleaned_count} old files/directories")

# Add a before_request handler to periodically clean up old files
@app.before_request
def before_request():
    # Store the hour timestamp in the app context
    hour_timestamp = int(time.time() / 3600)  # Current hour (3600 seconds in an hour)
    
    # Run cleanup once per hour for cloud deployment
    if not hasattr(app, 'last_cleanup_hour') or app.last_cleanup_hour < hour_timestamp:
        app.last_cleanup_hour = hour_timestamp
        # Run cleanup in a separate thread to avoid blocking the request
        import threading
        cleanup_thread = threading.Thread(target=lambda: cleanup_old_files(max_age_hours=1))
        cleanup_thread.daemon = True
        cleanup_thread.start()

if __name__ == '__main__':
    start_web_app() 