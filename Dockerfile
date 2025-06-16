FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload and output directories
RUN mkdir -p uploads output
RUN chmod 777 uploads output

# Set environment variables
ENV FLASK_APP=src.app_fixed
ENV PYTHONUNBUFFERED=1
ENV RENDER=true

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "run.py", "--web"] 