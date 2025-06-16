# CASA-Lite

A computer vision-based tool for analyzing fish sperm motility and quality parameters, designed as an affordable alternative to commercial CASA systems.

## Documentation

Visit our documentation site: [https://temabef.github.io/CASA-Lite/](https://temabef.github.io/CASA-Lite/)

## Overview

CASA-Lite analyzes fish sperm motility using computer vision techniques. It can process microscopy videos to:
- Track individual sperm cells
- Calculate motility parameters (VCL, VSL, LIN, etc.)
- Generate visual reports and statistics
- Provide a simple web interface for analysis

## Features

- **Video Processing**: Extract and process frames from microscopy videos
- **Sperm Tracking**: Advanced algorithm to track individual sperm cells across frames
- **Motility Analysis**: Calculate key motility parameters:
  - Total and motile sperm count
  - Curvilinear velocity (VCL)
  - Straight-line velocity (VSL)
  - Average path velocity (VAP)
  - Linearity (LIN)
  - Wobble (WOB)
  - Beat-cross frequency (BCF)
- **Visualization**: Generate plots and reports including:
  - Trajectory visualization
  - Velocity distribution histograms
  - HTML reports with comprehensive analysis
- **Web Interface**: Flask-based interface to upload and process videos

## Installation

### Prerequisites
- Python 3.8 or higher
- OpenCV
- NumPy, Matplotlib, Pandas

### Setup

1. Clone this repository:
```
git clone https://github.com/yourusername/CASA-Lite.git
cd CASA-Lite
```

2. Install dependencies:
```
pip install -r requirements.txt
```

## Usage

### Command Line Interface

Process a video file:
```
python run.py --video path/to/video.mp4
```

Options:
- `--video`: Path to input video file
- `--output`: Directory to save results (default: "output")
- `--debug`: Enable debug mode with visualizations
- `--web`: Start web interface instead of processing a file

### Web Interface

Start the web interface:
```
python run.py --web
```

Then open a browser and navigate to:
```
http://localhost:5000
```

## Running the Application

### Windows
```
cd SpermAnalysis
python run.py --web
```

### Mac/Linux
```
cd SpermAnalysis
python3 run.py --web
```

## Calibration

For accurate measurements in μm/s:

1. Record a calibration video with a known scale
2. Measure the pixels-to-microns ratio
3. Update the `pixels_per_micron` parameter in `src/analysis.py`

## Project Notes

CASA-Lite was previously known as "Automated Sperm Analysis System" during development. All references have been updated to reflect the new name.

The name CASA-Lite stands for "Computer-Assisted Sperm Analysis - Lite" and represents an affordable, accessible alternative to expensive commercial CASA systems.

## References

This project is inspired by commercial CASA (Computer-Assisted Sperm Analysis) systems and research in aquaculture reproduction.

## Author

Developed by Saheed Kolawole 