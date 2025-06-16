#!/usr/bin/env bash

# Exit on error
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories if they don't exist
echo "Setting up directories..."
mkdir -p output
mkdir -p uploads

# Any other setup steps can go here

echo "Build completed successfully!" 