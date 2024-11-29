import os
import re
import sys
import numpy as np
import matplotlib.pyplot as plt
import time

from scipy.spatial import ConvexHull

# Add the modules folder to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../modules")))

from data_processing import parse_ascii_file, process_binary_files_sequential
from compute_directions import compute_directions
from transformation import (
    transform_to_local,
    compute_angular_deviation,
    compute_local_coordinate_system,
)

from visualization import (
    plot_angular_distribution,
    plot_power_azimuth,
    plot_power_zenith,
    plot_power_zenith_asymmetric,
    plot_polar_distribution_of_rays_with_hull,
    plot_polar_power_distribution_with_hull,
    plot_polar_normalized_power_distribution
)

if __name__ == "__main__":
    start_time = time.time()  # Start measuring total execution time

    # Setup
    ascii_file = "data/photons_parameters.txt"
    binary_dir = "data"
    surface_id = int(input("Enter the Surface ID of interest: "))
    azimuth = 0.0
    elevation = -27.0

    # Compute local coordinate system
    local_x, local_y, local_z = compute_local_coordinate_system(azimuth, elevation)

    # Verify local coordinate system
    print("Local Coordinate System:")
    print(f"local_x: {local_x}")
    print(f"local_y: {local_y}")
    print(f"local_z: {local_z}")

    # Define the reference vector in the local coordinate system
    local_reference_vector = np.array([0, 0, 1])

    # Parse ASCII file
    ascii_start = time.time()
    parameter_names, surfaces, power_per_photon = parse_ascii_file(ascii_file)
    num_parameters = len(parameter_names)
    ascii_end = time.time()
    print(f"Time to parse ASCII file: {ascii_end - ascii_start:.2f} seconds")

    # Detect binary files
    binary_files = sorted(
        [os.path.join(binary_dir, f) for f in os.listdir(binary_dir) if re.match(r"photons.*\.dat", f)]
    )
    total_binary_size = sum(os.path.getsize(f) for f in binary_files)
    print(f"Total binary file size: {total_binary_size / (1024**2):.2f} MB")

    # Photon filtering
    filtering_start = time.time()
    filtered_photon_records = process_binary_files_sequential(binary_files, num_parameters, surface_id)
    filtering_end = time.time()
    print(f"Time to filter photons: {filtering_end - filtering_start:.2f} seconds")
    print(f"Filtered photon records: {len(filtered_photon_records)}")

    # Compute global direction vectors
    directions_start = time.time()
    directions = compute_directions(filtered_photon_records)
    directions_end = time.time()
    print(f"Time to compute directions: {directions_end - directions_start:.2f} seconds")

    # Transform directions to the local coordinate system
    local_directions_start = time.time()
    local_directions = transform_to_local(directions, local_x, local_y, local_z)
    local_directions_end = time.time()
    print(f"Time to transform directions to local coordinates: {local_directions_end - local_directions_start:.2f} seconds")

    # Compute angular deviations in the local coordinate system
    angular_start = time.time()
    angular_deviations = compute_angular_deviation(local_directions, local_reference_vector)
    angular_end = time.time()
    print(f"Time to compute angular deviations: {angular_end - angular_start:.2f} seconds")

    # Report statistics
    total_photons = total_binary_size // (num_parameters * 8)
    total_surface_photons = len(filtered_photon_records)
    total_directions = len(local_directions)

    print("\n=== Photon Processing Report ===")
    print(f"1. Total number of photons processed: {total_photons}")
    print(f"2. Total binary data size processed: {total_binary_size / (1024**2):.2f} MB")
    print(f"3. Total number of photons on the selected surface: {total_surface_photons}")
    print(f"4. Total number of direction vectors: {total_directions}")
    print(f"\nAverage Angular Deviation: {np.mean(angular_deviations):.2f} degrees")

    # Visualization
    bins = 50
    visualization_start = time.time()
    plot_polar_distribution_of_rays_with_hull(local_directions)
    plot_polar_power_distribution_with_hull(local_directions, power_per_photon, bins)
    plot_polar_normalized_power_distribution(local_directions, power_per_photon, bins)
    plot_angular_distribution(angular_deviations, power_per_photon, bins)  # Angular deviation histogram
    plot_power_azimuth(local_directions, power_per_photon, bins)
    plot_power_zenith(local_directions, power_per_photon, bins)
    plot_power_zenith_asymmetric(local_directions, power_per_photon, bins)
    visualization_end = time.time()
    print(f"Time for visualization: {visualization_end - visualization_start:.2f} seconds")

    # Total execution time
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds")
    plt.show()  # Keep all figures open