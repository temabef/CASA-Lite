#!/usr/bin/env python3
"""
Script to modify the application to use simulated data on Render.com
"""

import os
import re

def add_render_check_to_app():
    """Add Render environment check and simulated data function to app_fixed.py"""
    app_file = 'src/app_fixed.py'
    
    with open(app_file, 'r') as f:
        content = f.read()
    
    # Add IS_RENDER check if not already present
    if 'IS_RENDER = os.environ.get(\'RENDER\') == \'true\'' not in content:
        import_section = 'from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, send_from_directory, session'
        new_import = 'from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, send_from_directory, session\nimport psutil\nimport sys\nimport gc\nimport platform\n\n# Check if running on Render.com\nIS_RENDER = os.environ.get(\'RENDER\') == \'true\''
        content = content.replace(import_section, new_import)
    
    # Add simulated data function if not already present
    if 'def generate_simulated_data(' not in content:
        process_video_route = '@app.route(\'/process\')\ndef process_video():'
        simulated_data_function = '''@app.route('/process')
def process_video():'''
        
        simulated_function = '''def generate_simulated_data(debug=False):
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

@app.route('/process')
def process_video():'''
        
        content = content.replace(process_video_route, simulated_function)
    
    # Add environment check endpoint if not already present
    if '@app.route(\'/check-environment\')' not in content:
        about_route = '@app.route(\'/about\')\ndef about():'
        about_route_with_check = '''@app.route('/about')
def about():
    """Show about page"""
    logger.info("Rendering about page")
    return render_template('about.html')

@app.route('/check-environment')
def check_environment():
    """Check if running on Render.com"""
    return jsonify({
        'is_render': IS_RENDER
    })'''
        content = content.replace(about_route, about_route_with_check)
    
    # Modify analyze route to use simulated data on Render
    if 'if IS_RENDER:' not in content:
        analyze_pattern = r'# Process video\s+logger\.info\(f"Starting analysis of \{filepath\}"\)\s+start_time = time\.time\(\)\s+# Actual video processing implementation'
        analyze_replacement = '''# Process video
        logger.info(f"Starting analysis of {filepath}")
        start_time = time.time()
        
        # If running on Render, use simulated data instead of processing the video
        if IS_RENDER:
            logger.info("Running on Render - using simulated data instead of processing video")
            tracks, results = generate_simulated_data(debug=debug)
        else:
            # Actual video processing implementation'''
        
        content = re.sub(analyze_pattern, analyze_replacement, content)
    
    # Save changes
    with open(app_file, 'w') as f:
        f.write(content)
    
    print(f"Updated {app_file} with Render check and simulated data function")

def update_process_html():
    """Add notification banner to process.html"""
    html_file = 'templates/process.html'
    
    with open(html_file, 'r') as f:
        content = f.read()
    
    # Add render notice if not already present
    if 'id="renderNotice"' not in content:
        pattern = r'<div class="container">\s+<h1>Processing Video - CASA-Lite</h1>\s+<p>Analyzing file: <strong>\{\{ filename \}\}</strong></p>'
        replacement = '''<div class="container">
        <h1>Processing Video - CASA-Lite</h1>
        <p>Analyzing file: <strong>{{ filename }}</strong></p>
        
        <div id="renderNotice" style="background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin-bottom: 15px; display: none;">
            <strong>Demo Mode:</strong> This Render deployment uses simulated data instead of processing actual video files to conserve resources. For full functionality, please run the application locally.
        </div>'''
        
        content = re.sub(pattern, replacement, content)
    
    # Add JavaScript to check environment
    if 'fetch(\'/check-environment\')' not in content:
        pattern = r'document\.addEventListener\(\'DOMContentLoaded\', function\(\) \{\s+const analysisForm = document\.getElementById\(\'analysisOptions\'\);'
        replacement = '''document.addEventListener('DOMContentLoaded', function() {
            const analysisForm = document.getElementById('analysisOptions');
            
            // Check if running on Render.com (will be determined by server)
            fetch('/check-environment')
                .then(response => response.json())
                .then(data => {
                    if (data.is_render) {
                        document.getElementById('renderNotice').style.display = 'block';
                    }
                })
                .catch(error => console.error('Error checking environment:', error));'''
        
        content = re.sub(pattern, replacement, content)
    
    # Save changes
    with open(html_file, 'w') as f:
        f.write(content)
    
    print(f"Updated {html_file} with Render notification")

def update_index_html():
    """Add notification banner to index.html"""
    html_file = 'templates/index.html'
    
    with open(html_file, 'r') as f:
        content = f.read()
    
    # Add render notice if not already present
    if 'id="render-notice"' not in content:
        pattern = r'<div class="container">\s+<h1>CASA-Lite</h1>\s+<p class="tagline">An affordable Computer-Assisted Sperm Analysis Tool for fish reproduction research</p>'
        replacement = '''<div class="container">
        <h1>CASA-Lite</h1>
        <p class="tagline">An affordable Computer-Assisted Sperm Analysis Tool for fish reproduction research</p>
        
        <div id="render-notice" style="background-color: #cce5ff; color: #004085; padding: 15px; border-radius: 5px; margin: 20px 0; display: none;">
            <strong>Demo Mode:</strong> This Render deployment uses simulated data instead of processing actual video files to conserve resources. For full functionality, please run the application locally. <a href="https://github.com/temabef/CASA-Lite" target="_blank">Get the code on GitHub</a>.
        </div>'''
        
        content = re.sub(pattern, replacement, content)
    
    # Add JavaScript to check environment
    if 'fetch(\'/check-environment\')' not in content:
        pattern = r'document\.addEventListener\(\'DOMContentLoaded\', function\(\) \{\s+const form = document\.getElementById\(\'upload-form\'\);'
        replacement = '''document.addEventListener('DOMContentLoaded', function() {
            const form = document.getElementById('upload-form');
            
            // Check if running on Render.com
            fetch('/check-environment')
                .then(response => response.json())
                .then(data => {
                    if (data.is_render) {
                        document.getElementById('render-notice').style.display = 'block';
                    }
                })
                .catch(error => console.error('Error checking environment:', error));'''
        
        content = re.sub(pattern, replacement, content)
    
    # Save changes
    with open(html_file, 'w') as f:
        f.write(content)
    
    print(f"Updated {html_file} with Render notification")

def update_dockerfile():
    """Add RENDER environment variable to Dockerfile"""
    dockerfile = 'Dockerfile'
    
    with open(dockerfile, 'r') as f:
        content = f.read()
    
    # Add RENDER environment variable if not already present
    if 'ENV RENDER=true' not in content:
        pattern = r'# Set environment variables\s+ENV FLASK_APP=src\.app_fixed\s+ENV PYTHONUNBUFFERED=1'
        replacement = '''# Set environment variables
ENV FLASK_APP=src.app_fixed
ENV PYTHONUNBUFFERED=1
ENV RENDER=true'''
        
        content = re.sub(pattern, replacement, content)
    
    # Save changes
    with open(dockerfile, 'w') as f:
        f.write(content)
    
    print(f"Updated {dockerfile} with RENDER environment variable")

def main():
    """Apply all changes"""
    print("Switching to simulated data for Render deployment...")
    
    add_render_check_to_app()
    update_process_html()
    update_index_html()
    update_dockerfile()
    
    print("All changes applied successfully!")
    print("Remember to commit and push these changes to trigger redeployment on Render.")

if __name__ == "__main__":
    main() 