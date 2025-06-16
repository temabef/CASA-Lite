# CASA-Lite Deployment Guide

This guide provides instructions for deploying the CASA-Lite application in both development and production environments.

## Prerequisites

- Python 3.8+ installed
- pip (Python package manager)
- Git (for cloning the repository)
- OpenCV dependencies (for image processing)
- A web server for production deployment (e.g., Nginx, Apache)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/temabef/CASA-Lite.git
cd CASA-Lite
```

### 2. Create a Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Development Server

```bash
python run.py --web
```

The application will be available at http://127.0.0.1:5000.

## Production Deployment

For production environments, it's recommended to use a WSGI server like Gunicorn with a reverse proxy like Nginx.

### 1. Install Additional Requirements

```bash
pip install gunicorn
```

### 2. Create a WSGI Entry Point

Create a file named `wsgi.py` in the root directory:

```python
from src.app_fixed import app

if __name__ == "__main__":
    app.run()
```

### 3. Configure Gunicorn

Create a file named `gunicorn_config.py`:

```python
bind = "127.0.0.1:8000"
workers = 4  # Adjust based on your server resources
timeout = 120  # Increased timeout for video processing
max_requests = 1000
max_requests_jitter = 50
```

### 4. Set Up Nginx as a Reverse Proxy

Install Nginx and create a configuration file `/etc/nginx/sites-available/casa-lite`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
        client_max_body_size 500M;  # Match the Flask upload limit
    }

    location /static {
        alias /path/to/CASA-Lite/static;
        expires 30d;
    }
}
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/casa-lite /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

### 5. Run with Gunicorn

```bash
gunicorn -c gunicorn_config.py wsgi:app
```

### 6. Set Up a Systemd Service (Optional)

Create a file `/etc/systemd/system/casa-lite.service`:

```ini
[Unit]
Description=CASA-Lite Gunicorn Service
After=network.target

[Service]
User=your-username
Group=your-group
WorkingDirectory=/path/to/CASA-Lite
Environment="PATH=/path/to/CASA-Lite/venv/bin"
ExecStart=/path/to/CASA-Lite/venv/bin/gunicorn -c gunicorn_config.py wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable casa-lite
sudo systemctl start casa-lite
```

## Docker Deployment (Alternative)

### 1. Create a Dockerfile

Create a file named `Dockerfile` in the root directory:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload and output directories
RUN mkdir -p uploads output
RUN chmod 777 uploads output

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "run.py", "--web"]
```

### 2. Create a Docker Compose File

Create a file named `docker-compose.yml`:

```yaml
version: '3'

services:
  casa-lite:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./uploads:/app/uploads
      - ./output:/app/output
    restart: always
```

### 3. Build and Run with Docker Compose

```bash
docker-compose up -d
```

## Configuration Options

### Environment Variables

You can configure the application using environment variables:

- `FLASK_ENV`: Set to `development` or `production`
- `FLASK_SECRET_KEY`: Secret key for session encryption
- `MAX_UPLOAD_SIZE`: Maximum upload size in megabytes (default: 500)
- `UPLOAD_FOLDER`: Path to upload directory
- `OUTPUT_FOLDER`: Path to output directory

### Application Performance Tuning

For better performance with large videos:

1. Adjust the `max_frames` parameter to limit the number of frames processed
2. Increase the worker timeout in Gunicorn for processing large files
3. Consider using a dedicated server with GPU support for faster processing

## Security Considerations

1. Set a strong secret key for Flask sessions
2. Use HTTPS in production (configure SSL in Nginx)
3. Implement rate limiting for uploads
4. Validate file types and sizes on both client and server
5. Consider implementing user authentication for multi-user environments

## Troubleshooting

### Common Issues

1. **Upload failures**: Check the maximum upload size in both Flask and Nginx configurations
2. **Processing errors**: Ensure OpenCV dependencies are properly installed
3. **Permission issues**: Check directory permissions for uploads and output folders
4. **Memory errors**: Increase available memory or reduce the number of frames processed

### Logs

- Application logs: Check the application's log output
- Nginx logs: `/var/log/nginx/error.log` and `/var/log/nginx/access.log`
- Gunicorn logs: Available in systemd journal if using systemd service

## Maintenance

1. Regularly backup the output directory containing analysis results
2. Monitor disk usage as video files can consume significant space
3. Set up log rotation for application logs
4. Update dependencies regularly for security patches

## Support

For issues and support, please visit the [GitHub repository](https://github.com/temabef/CASA-Lite/issues). 