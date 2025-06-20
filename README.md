﻿# CASA-Lite: Computer-Assisted Sperm Analysis Tool

CASA-Lite is an affordable, open-source tool designed to analyze fish sperm motility using computer vision techniques. This project aims to provide researchers and aquaculture professionals with accessible tools for reproductive biology research without the need for expensive commercial systems.

## Overview

Traditional Computer-Assisted Sperm Analysis (CASA) systems can cost thousands of dollars, making them inaccessible for many researchers, especially in developing countries. CASA-Lite bridges this gap by providing a free, web-based alternative that requires only a standard microscope with video recording capabilities.

![CASA-Lite Screenshot](static/images/screenshot.svg)

## Features

- **Track Individual Sperm Cells**: Automatically detect and track sperm movement across frames
- **Calculate Motility Parameters**: VCL, VSL, LIN, and more key parameters
- **Generate Visual Reports**: Trajectories, velocity distributions, and detailed analysis
- **Simple Interface**: Easy to use without specialized training
- **Resource Efficient**: Optimized for standard computers without specialized hardware
- **Modern UI**: Responsive design works on desktop and mobile devices
- **Comprehensive Reports**: Detailed PDF reports with visualizations

## Motility Parameters Calculated

- **VCL** (Curvilinear Velocity): Total distance traveled by sperm along its actual path per unit time
- **VSL** (Straight-Line Velocity): Straight-line distance from first to last position divided by time
- **VAP** (Average Path Velocity): Distance traveled along an average path per unit time
- **LIN** (Linearity): Ratio of VSL to VCL (straightness of path)
- **WOB** (Wobble): Ratio of VAP to VCL (oscillation of actual path)
- **PROG** (Progression): Ratio of VSL to VAP
- **BCF** (Beat-Cross Frequency): Frequency of sperm head crossing the average path

## How It Works

1. **Video Processing**: The system processes microscopy videos of sperm samples
2. **Cell Detection**: Computer vision algorithms identify individual sperm cells in each frame
3. **Tracking**: Cells are tracked across multiple frames to create movement paths
4. **Analysis**: Motility parameters are calculated from the tracking data
5. **Visualization**: Results are presented in an interactive web interface with detailed reports

## Technical Implementation

CASA-Lite is built using:
- **Python**: Core programming language
- **OpenCV**: Computer vision library for video processing and analysis
- **NumPy**: Numerical computing for data analysis
- **Flask**: Web framework for the user interface
- **Matplotlib**: Data visualization library
- **Pandas**: Data manipulation and analysis

The application follows a modular architecture with separate components for:
- Video preprocessing
- Sperm detection and tracking
- Motility analysis
- Visualization and reporting
- Web interface

## LIVE URL: [CASA-Lite](https://casa-lite.onrender.com/) 
## Quick Start

### Using Docker (Recommended)

The easiest way to run CASA-Lite is using Docker:

```bash
# Clone the repository
git clone https://github.com/temabef/CASA-Lite.git
cd CASA-Lite

# Build and start the Docker container
docker-compose up -d

# Access the application at http://localhost:5000
```

### Manual Installation

#### Prerequisites

- Python 3.8 or higher
- OpenCV dependencies
- Git

#### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/temabef/CASA-Lite.git
   cd CASA-Lite
   ```

2. Create a virtual environment:
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   
   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python run.py --web
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage Guide

1. **Upload Video**: Select a microscopy video file (MP4, AVI, MOV, or WMV format)
2. **Configure Analysis**: Set the maximum number of frames to process
3. **Start Analysis**: Click "Upload & Analyze" to begin processing
4. **View Results**: Explore the generated report with motility parameters and visualizations
5. **Download Report**: Save or print the detailed report for your records

## Deployment

For production deployment, see the [Deployment Guide](DEPLOYMENT.md) which includes:

- Setting up with Nginx and Gunicorn
- Docker deployment options
- Configuration and security considerations
- Performance tuning

## Development

### Project Structure

```
CASA-Lite/
├── src/                  # Source code
│   ├── app_fixed.py      # Flask application
│   ├── video_processor.py # Video processing module
│   ├── sperm_tracker.py  # Sperm tracking algorithms
│   └── visualization.py  # Data visualization
├── static/               # Static assets
├── templates/            # HTML templates
├── uploads/              # Uploaded videos
├── output/               # Analysis results
├── run.py                # Entry point
└── requirements.txt      # Dependencies
```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## About the Developer

Saheed Kolawole is a Nigerian student studying aquaculture in Turkey. With a passion for both fisheries science and technology, he developed CASA-Lite to address the need for affordable sperm analysis tools in aquaculture research.

## Scientific Background

Sperm motility analysis is a critical component in assessing male fertility in both human medicine and animal reproduction research. In aquaculture specifically, sperm quality assessment helps optimize artificial breeding programs, cryopreservation protocols, and overall reproductive management.

The analysis involves tracking individual sperm cells and measuring various movement parameters that correlate with fertilization potential. These parameters include velocity measurements, path linearity, and beat frequency, among others.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Wilson-Leedy, J. G., & Ingermann, R. L. (2007). Development of a novel CASA system based on open source software for characterization of zebrafish sperm motility parameters.
- OpenCV community for the excellent computer vision library
- Flask team for the web framework
