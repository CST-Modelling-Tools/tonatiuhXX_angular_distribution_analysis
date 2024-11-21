import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np


def plot_angular_distribution(angular_deviations, output_file="angular_distribution.png"):
    plt.figure(figsize=(8, 6))
    plt.hist(angular_deviations, bins=50, color='blue', alpha=0.7)
    plt.title("Angular Distribution of Photons")
    plt.xlabel("Angular Deviation (degrees)")
    plt.ylabel("Frequency")
    plt.grid()
    plt.savefig(output_file)
    print(f"Plot saved to {output_file}")
    plt.show(block=False)  # Allow multiple figures


def plot_directions_on_unit_sphere(directions):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 50)
    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones_like(u), np.cos(v))
    ax.plot_surface(x, y, z, color='lightblue', alpha=0.3, edgecolor='w')
    ax.scatter(directions[:, 0], directions[:, 1], directions[:, 2],
               color='red', s=10, alpha=0.8, label="Photon Directions")
    ax.set_title("Photon Direction Distribution on Unit Sphere", fontsize=16)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.legend()
    plt.show(block=False)  # Allow multiple figures


def plot_direction_density_heatmap(directions, bins=100):
    azimuth = np.arctan2(directions[:, 0], directions[:, 1])
    elevation = np.arcsin(directions[:, 2])
    hist, xedges, yedges = np.histogram2d(azimuth, elevation, bins=bins, density=True)
    xcenters = (xedges[:-1] + xedges[1:]) / 2
    ycenters = (yedges[:-1] + yedges[1:]) / 2
    x, y = np.meshgrid(xcenters, ycenters)
    plt.figure(figsize=(10, 8))
    plt.contourf(x, y, hist.T, levels=100, cmap='inferno')
    plt.colorbar(label='Density')
    plt.title("Photon Direction Density Heatmap (Spherical Coordinates)", fontsize=16)
    plt.xlabel("Azimuth (radians)")
    plt.ylabel("Elevation (radians)")
    plt.show(block=False)  # Allow multiple figures