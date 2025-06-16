#!/usr/bin/env python3
"""
Create a simple favicon for the CASA-Lite application
"""

import os
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

def create_favicon():
    """Create a simple favicon"""
    favicon_path = 'static/favicon.ico'
    
    # Create a simple favicon
    plt.figure(figsize=(1, 1), dpi=16)
    plt.axis('off')
    circle = plt.Circle((0.5, 0.5), 0.4, color='#3498db')
    plt.gca().add_patch(circle)
    plt.gca().set_aspect('equal')
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    
    # Save as PNG first
    temp_path = 'static/temp_favicon.png'
    plt.savefig(temp_path, format='png', transparent=False)
    plt.close()
    
    # Convert to ICO
    img = Image.open(temp_path)
    img.save(favicon_path, format='ICO', sizes=[(16, 16)])
    
    # Clean up temporary file
    os.remove(temp_path)
    print(f"Created favicon at {favicon_path}")

if __name__ == "__main__":
    create_favicon() 