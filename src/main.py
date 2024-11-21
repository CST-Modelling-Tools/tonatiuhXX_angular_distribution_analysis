import os
import re
import numpy as np
import matplotlib.pyplot as plt
from data_processing import parse_ascii_file, process_binary_files_sequential
from transformation import (
    spherical_to_cartesian,
    compute_directions,
    transform_to_local,
    compute_angular_deviation,
    compute_local_coordinate_system
)

from visualization import (
    plot_angular_distribution,
    plot_directions_on_unit_sphere,
    plot_direction_density_heatmap
)

if __name__ == "__main__":
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

    # File parsing
    parameter_names, surfaces, power_per_photon = parse_ascii_file(ascii_file)
    num_parameters = len(parameter_names)
    binary_files = sorted(
        [os.path.join(binary_dir, f) for f in os.listdir(binary_dir) if re.match(r"photons.*\.dat", f)]
    )

    # Photon filtering using trajectory-based filtering
    filtered_photon_records = process_binary_files_sequential(binary_files, num_parameters, surface_id)

    # Compute global direction vectors
    directions = compute_directions(filtered_photon_records)

    # Transform directions to the local coordinate system
    local_directions = transform_to_local(directions, local_x, local_y, local_z)

    # Check sample of directions
    print("\nSample Directions (Global to Local):")
    for i in range(min(10, len(directions))):
        print(f"Global: {directions[i]}, Local: {local_directions[i]}")

    # Compute angular deviations in the local coordinate system
    angular_deviations = compute_angular_deviation(local_directions, local_reference_vector)

    # Report statistics
    total_photons = sum(
        os.path.getsize(f) // (num_parameters * 8) for f in binary_files
    )
    total_surface_photons = len(filtered_photon_records)
    total_directions = len(local_directions)

    print("\n=== Photon Processing Report ===")
    print(f"1. Total number of photons processed: {total_photons}")
    print(f"2. Total number of photons on the selected surface: {total_surface_photons}")
    print(f"3. Total number of direction vectors: {total_directions}")
    print(f"\nAverage Angular Deviation: {np.mean(angular_deviations):.2f} degrees")

    # Visualization
    plot_angular_distribution(angular_deviations)  # Angular deviation histogram
    plot_directions_on_unit_sphere(local_directions)  # 3D sphere plot of direction vectors
    plot_direction_density_heatmap(local_directions)  # 2D heatmap of direction vectors

    plt.show()  # Keep all figures open
