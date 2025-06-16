# Pre-Deployment Cleanup Recommendations

After reviewing the codebase, here are the files that can be safely deleted before deployment:

## Source Code Duplicates

1. `src/app.py` - The original app file with encoding issues. We're now using `app_fixed.py` which is properly imported in `main.py` and `wsgi.py`.
2. `src/app_clean.py` - An intermediate version, not used anywhere in the codebase
3. `src/app_fixed_with_viz.py` - Features have been merged into `app_fixed.py`, no longer needed
4. `src/video_processor_new.py` - Likely an experimental version. The main code uses `video_processor.py`
5. `src/temp.txt` - Temporary file that should be removed

## Test Data Files

The `uploads` directory contains multiple copies of the same videos with different prefixes:
1. Remove duplicate test videos like those with UUID prefixes (e.g., `1afa5f73e70743898cbca3fa05a09417_3y7dK1-1.avi`)
2. Keep only one sample video for testing

## Generated Output

1. Clear the `output` directory of any pre-existing analysis results
   
## Other Recommendations

1. Add a `.gitignore` file to exclude uploads and output directories from version control
2. Remove any `__pycache__` directories (already excluded from git)
3. Clear any log files that may have accumulated during development

## Files to Keep

1. `src/app_fixed.py` - The main application
2. `src/video_processor.py` - The video processing module
3. `src/sperm_tracker.py` - The sperm tracking module
4. All template and static files
5. Docker-related files, requirements.txt, and main.py

These changes will make the codebase cleaner and more maintainable for deployment. 