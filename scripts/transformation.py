import numpy as np
import os
import sys

# Ensure the modules folder is in the Python path to import the .pyd module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../modules")))

from compute_directions import compute_directions  # Import from the .pyd module


def spherical_to_cartesian(azimuth, elevation):
    """
    Converts spherical coordinates (azimuth, elevation) to a Cartesian unit vector.

    Args:
        azimuth (float): Azimuth angle in degrees (measured from y-axis towards x-axis).
        elevation (float): Elevation angle in degrees (measured from the horizontal plane).

    Returns:
        np.ndarray: Cartesian unit vector [x, y, z].
    """
    azimuth_rad = np.radians(azimuth)
    elevation_rad = np.radians(elevation)

    x = np.cos(elevation_rad) * np.sin(azimuth_rad)
    y = np.cos(elevation_rad) * np.cos(azimuth_rad)
    z = np.sin(elevation_rad)

    return np.array([x, y, z])


def compute_angular_deviation(direction_vectors, reference_vector):
    """
    Computes the angular deviation of photon directions from a reference vector.

    Args:
        direction_vectors (np.ndarray): Array of normalized direction vectors.
        reference_vector (np.ndarray): Reference vector.

    Returns:
        np.ndarray: Array of angular deviations (in degrees).
    """
    # Compute dot product
    dot_products = np.dot(direction_vectors, reference_vector)

    # Clip values to [-1, 1] for safety
    dot_products = np.clip(dot_products, -1.0, 1.0)

    # Compute angular deviations
    angular_deviations = np.degrees(np.arccos(dot_products))

    return angular_deviations


def compute_local_coordinate_system(azimuth, elevation):
    """
    Computes the local coordinate system (x, y, z) based on azimuth and elevation.

    Args:
        azimuth (float): Azimuth angle in degrees (measured from y-axis towards x-axis).
        elevation (float): Elevation angle in degrees (measured from the horizontal plane).

    Returns:
        tuple: (local_x, local_y, local_z) as unit vectors in the global coordinate system.
    """
    # Define the local z-axis (normal to the surface)
    local_z = spherical_to_cartesian(azimuth, elevation)

    # Define the local x-axis (parallel to the horizontal plane)
    azimuth_rad = np.radians(azimuth)
    local_x = np.array([np.cos(azimuth_rad), np.sin(azimuth_rad), 0])
    local_x /= np.linalg.norm(local_x)  # Ensure normalization

    # Define the local y-axis (orthogonal to x and z)
    local_y = np.cross(local_z, local_x)
    local_y /= np.linalg.norm(local_y)  # Ensure normalization

    return local_x, local_y, local_z


def transform_to_local(directions, local_x, local_y, local_z):
    """
    Transforms direction vectors into the local coordinate system.

    Args:
        directions (np.ndarray): Array of global direction vectors.
        local_x (np.ndarray): Local x-axis unit vector in the global coordinate system.
        local_y (np.ndarray): Local y-axis unit vector in the global coordinate system.
        local_z (np.ndarray): Local z-axis unit vector in the global coordinate system.

    Returns:
        np.ndarray: Array of direction vectors in the local coordinate system.
    """
    # Create a rotation matrix from the local axes
    rotation_matrix = np.array([local_x, local_y, local_z]).T

    # Transform directions into the local coordinate system
    local_directions = directions @ rotation_matrix

    return local_directions