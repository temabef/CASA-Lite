#!/usr/bin/env python3
"""
Create sample trajectory and velocity images for the demo mode.
"""

import os
import numpy as np
import matplotlib.pyplot as plt

def create_sample_trajectory():
    """Create a sample trajectory image"""
    plt.figure(figsize=(8, 6))
    
    # Generate some sample trajectory data
    num_tracks = 20
    colors = plt.cm.jet(np.linspace(0, 1, num_tracks))
    
    for i in range(num_tracks):
        # Create a random trajectory
        x = np.cumsum(np.random.normal(0, 2, 30))
        y = np.cumsum(np.random.normal(0, 2, 30))
        
        # Plot the trajectory
        plt.plot(x, y, color=colors[i], alpha=0.7, linewidth=1.5)
        plt.scatter(x[0], y[0], color=colors[i], s=30, marker='o')  # Start point
        plt.scatter(x[-1], y[-1], color=colors[i], s=50, marker='*')  # End point
    
    plt.title("Sperm Trajectories (n=20)")
    plt.xlabel("X position (pixels)")
    plt.ylabel("Y position (pixels)")
    plt.grid(alpha=0.3)
    
    # Save to file
    os.makedirs('static/images', exist_ok=True)
    img_path = 'static/images/sample_trajectory.png'
    plt.savefig(img_path, dpi=100, format='png', bbox_inches='tight', pad_inches=0.1)
    plt.close()
    
    print(f"Created sample trajectory image: {img_path}")

def create_sample_velocity():
    """Create a sample velocity distribution image"""
    fig, ax = plt.subplots(1, 3, figsize=(12, 4))
    
    # Generate sample data
    vcl_data = np.random.normal(50, 10, 100)
    vsl_data = np.random.normal(30, 6, 100)
    lin_data = np.random.beta(5, 3, 100)
    
    # Plot VCL (curvilinear velocity)
    ax[0].hist(vcl_data, bins=15, color='blue', alpha=0.7)
    ax[0].set_title('Curvilinear Velocity (VCL)')
    ax[0].set_xlabel('Velocity (μm/s)')
    ax[0].axvline(np.mean(vcl_data), color='red', linestyle='dashed', linewidth=2)
    
    # Plot VSL (straight-line velocity)
    ax[1].hist(vsl_data, bins=15, color='green', alpha=0.7)
    ax[1].set_title('Straight-line Velocity (VSL)')
    ax[1].set_xlabel('Velocity (μm/s)')
    ax[1].axvline(np.mean(vsl_data), color='red', linestyle='dashed', linewidth=2)
    
    # Plot linearity
    ax[2].hist(lin_data, bins=15, color='red', alpha=0.7)
    ax[2].set_title('Linearity (LIN)')
    ax[2].set_xlabel('Linearity Index')
    ax[2].axvline(np.mean(lin_data), color='blue', linestyle='dashed', linewidth=2)
    
    plt.tight_layout()
    
    # Save to file
    os.makedirs('static/images', exist_ok=True)
    img_path = 'static/images/sample_velocity.png'
    plt.savefig(img_path, dpi=100, format='png', bbox_inches='tight', pad_inches=0.1)
    plt.close()
    
    print(f"Created sample velocity image: {img_path}")

if __name__ == "__main__":
    print("Creating sample images for demo mode...")
    create_sample_trajectory()
    create_sample_velocity()
    print("Done!") 