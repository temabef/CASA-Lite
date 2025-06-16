# Data Directory

This directory should contain video files for analysis.

## Sample Data

To use this system, you'll need microscopy videos of fish sperm. Ideally, these should be:
- Recorded with a phase contrast microscope
- Magnification around 10-40x
- Frame rate of at least 30 fps
- Good contrast between sperm cells and background
- Short duration (5-15 seconds is typically sufficient)

## Recording Recommendations

For best results when recording sperm videos:

1. Use a standardized chamber depth (e.g., Leja slides)
2. Maintain consistent temperature during recording
3. Include a scale bar in at least one reference recording
4. Use phase contrast microscopy where possible
5. Record within 60 seconds of activation for most fish species
6. Use appropriate dilution to avoid too many overlapping tracks

## File Format

The system accepts the following video formats:
- MP4
- AVI
- MOV
- WMV

## Getting Started

Place your sperm microscopy videos in this directory, then run the analysis using:

```
python run.py --video data/your_video_file.mp4
``` 