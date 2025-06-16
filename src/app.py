"""
Web application module for CASA-Lite
"""

import os
import logging
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename

# Import from our modules
from src.video_processor import VideoProcessor
from src.sperm_tracker import SpermTracker
from src.analysis import MotilityAnalyzer
from src.visualization import Visualizer

# Create Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static'))

# Configure app
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv'}

# Ensure folders exist
Path(UPLOAD_FOLDER).mkdir(exist_ok=True, parents=True)
Path(OUTPUT_FOLDER).mkdir(exist_ok=True, parents=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
app.secret_key = 'sperm-analysis-secret-key'

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'video' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['video']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Save file information for later processing
        session_id = str(hash(filename + str(os.path.getmtime(filepath))))
        
        return redirect(url_for('process_video', filename=filename, session_id=session_id))
    
    flash('Invalid file type')
    return redirect(url_for('index'))

@app.route('/process/<filename>/<session_id>')
def process_video(filename, session_id):
    """Process video file"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        flash('File not found')
        return redirect(url_for('index'))
    
    # Create output directory for this session
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    
    return render_template('process.html', 
                          filename=filename,
                          filepath=filepath,
                          session_id=session_id)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Run analysis (AJAX endpoint)"""
    data = request.get_json()
    
    if not data or 'filepath' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    filepath = data['filepath']
    session_id = data.get('session_id', 'default')
    debug = data.get('debug', False)
    
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
    
    try:
        # Process video and track sperm
        video_processor = VideoProcessor(filepath, debug=debug)
        frames = video_processor.extract_frames()
        
        tracker = SpermTracker(debug=debug)
        tracks = tracker.track_sperm(frames)
        
        # Analyze motility
        analyzer = MotilityAnalyzer()
        results = analyzer.analyze(tracks)
        
        # Generate visualizations
        visualizer = Visualizer(output_dir=output_dir)
        visualizer.plot_trajectories(tracks)
        visualizer.plot_velocity_distribution(results)
        report_path = visualizer.generate_report(results)
        
        # Create results summary
        summary = {
            'total_count': results.total_count,
            'motile_count': results.motile_count,
            'motility_percent': results.motility_percent,
            'vcl': results.vcl,
            'vsl': results.vsl,
            'lin': results.lin,
            'report_url': url_for('results', session_id=session_id)
        }
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/results/<session_id>')
def results(session_id):
    """Show results page"""
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
    report_path = os.path.join(output_dir, 'report.html')
    
    if os.path.exists(report_path):
        return send_from_directory(output_dir, 'report.html')
    
    flash('Results not found')
    return redirect(url_for('index'))

def create_templates():
    """Create template files if they don't exist"""
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
    
    Path(template_dir).mkdir(exist_ok=True, parents=True)
    Path(static_dir).mkdir(exist_ok=True, parents=True)
    
    # Create index.html
    index_path = os.path.join(template_dir, 'index.html')
    if not os.path.exists(index_path):
        with open(index_path, 'w') as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>CASA-Lite: Computer-Assisted Sperm Analysis Tool</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; }
        h1 { color: #2c3e50; text-align: center; }
        .upload-form { margin: 30px 0; text-align: center; }
        .submit-btn { background-color: #3498db; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        .alert { padding: 10px; background-color: #f8d7da; color: #721c24; margin-bottom: 15px; }
        .footer { margin-top: 30px; text-align: center; font-size: 0.8em; color: #777; }
    </style>
</head>
<body>
    <div class="container">
        <h1>CASA-Lite</h1>
        <p>Upload a video file containing microscopy footage of sperm cells to analyze motility parameters.</p>
        
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <div class="alert">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        
        <div class="upload-form">
            <form action="/upload" method="post" enctype="multipart/form-data">
                <div>
                    <label for="video">Select video file:</label>
                    <input type="file" name="video" id="video">
                </div>
                <div>
                    <label><input type="checkbox" name="debug"> Debug mode</label>
                </div>
                <button type="submit" class="submit-btn">Upload & Analyze</button>
            </form>
        </div>
        
        <div class="footer">
            <p>CASA-Lite: An affordable Computer-Assisted Sperm Analysis Tool</p>
            <p>Developed by Saheed Kolawole</p>
        </div>
    </div>
</body>
</html>
            """)
    
    # Create process.html
    process_path = os.path.join(template_dir, 'process.html')
    if not os.path.exists(process_path):
        with open(process_path, 'w') as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Processing Video - CASA-Lite</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; }
        .progress { width: 100%; height: 20px; background-color: #f0f0f0; margin-bottom: 20px; }
        .progress-bar { height: 100%; background-color: #3498db; width: 0%; transition: width 0.5s; }
        .results { margin-top: 30px; display: none; }
        .results table { width: 100%; border-collapse: collapse; }
        .results th, .results td { border: 1px solid #ddd; padding: 8px; }
        .view-report { display: block; margin: 20px auto; padding: 10px 20px; background-color: #2ecc71; 
                      color: white; text-align: center; text-decoration: none; }
        .footer { margin-top: 30px; text-align: center; font-size: 0.8em; color: #777; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Processing Video - CASA-Lite</h1>
        <p>Analyzing file: <strong>{{ filename }}</strong></p>
        
        <div class="progress">
            <div class="progress-bar" id="progressBar"></div>
        </div>
        <div id="status">Initializing analysis...</div>
        
        <div class="results" id="results">
            <h2>Analysis Results</h2>
            <table>
                <tr><th>Parameter</th><th>Value</th></tr>
                <tr><td>Total Sperm Count</td><td id="totalCount">-</td></tr>
                <tr><td>Motile Sperm</td><td id="motileCount">-</td></tr>
                <tr><td>Motility Percentage</td><td id="motilityPercent">-</td></tr>
                <tr><td>Average VCL</td><td id="avgVCL">-</td></tr>
                <tr><td>Average VSL</td><td id="avgVSL">-</td></tr>
                <tr><td>Linearity</td><td id="lin">-</td></tr>
            </table>
            
            <a href="#" class="view-report" id="viewReport">View Full Report</a>
        </div>
        
        <div id="errorContainer" style="display: none;">
            <p id="errorMessage" style="color: red"></p>
            <p><a href="/">Go back to main page</a></p>
        </div>
        
        <div class="footer">
            <p>CASA-Lite: An affordable Computer-Assisted Sperm Analysis Tool</p>
            <p>Developed by Saheed Kolawole</p>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const progressBar = document.getElementById('progressBar');
            const statusText = document.getElementById('status');
            const resultsDiv = document.getElementById('results');
            const errorContainer = document.getElementById('errorContainer');
            const errorMessage = document.getElementById('errorMessage');
            const viewReportLink = document.getElementById('viewReport');
            
            // Simulate progress
            let progress = 0;
            const progressInterval = setInterval(() => {
                if (progress < 90) {
                    progress += Math.random() * 5;
                    progressBar.style.width = `${Math.min(progress, 90)}%`;
                }
            }, 500);
            
            statusText.textContent = "Processing video...";
            
            // Send AJAX request to analyze video
            fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filepath: '{{ filepath }}',
                    session_id: '{{ session_id }}',
                    debug: {{ 'true' if request.args.get('debug') else 'false' }}
                }),
            })
            .then(response => response.json())
            .then(data => {
                clearInterval(progressInterval);
                
                if (data.success) {
                    // Update progress to 100%
                    progressBar.style.width = '100%';
                    statusText.textContent = "Analysis complete!";
                    
                    // Display results
                    document.getElementById('totalCount').textContent = data.summary.total_count;
                    document.getElementById('motileCount').textContent = data.summary.motile_count;
                    document.getElementById('motilityPercent').textContent = 
                        `${data.summary.motility_percent.toFixed(1)}%`;
                    document.getElementById('avgVCL').textContent = 
                        `${data.summary.vcl.toFixed(2)} μm/s`;
                    document.getElementById('avgVSL').textContent = 
                        `${data.summary.vsl.toFixed(2)} μm/s`;
                    document.getElementById('lin').textContent = data.summary.lin.toFixed(2);
                    
                    // Set report link
                    viewReportLink.href = data.summary.report_url;
                    
                    // Show results
                    resultsDiv.style.display = 'block';
                } else {
                    statusText.textContent = "Analysis failed";
                    progressBar.style.backgroundColor = 'red';
                    errorMessage.textContent = data.error || "An error occurred";
                    errorContainer.style.display = 'block';
                }
            })
            .catch(error => {
                clearInterval(progressInterval);
                statusText.textContent = "Analysis failed";
                progressBar.style.backgroundColor = 'red';
                errorMessage.textContent = "Failed to communicate with server";
                errorContainer.style.display = 'block';
            });
        });
    </script>
</body>
</html>
            """)

def start_web_app(host='0.0.0.0', port=5000, debug=True):
    """Start the web application"""
    create_templates()
    app.run(host=host, port=port, debug=debug)
    
if __name__ == '__main__':
    start_web_app() 