import numpy as np
import os

def parse_ascii_file(ascii_file):
    """
    Parses the ASCII file to extract parameter names, surface definitions, and power per photon.
    Args:
        ascii_file (str): Path to the ASCII file.

    Returns:
        tuple: (parameter_names, surfaces, power_per_photon)
            - parameter_names: List of parameter names.
            - surfaces: Dictionary mapping surface IDs to URLs or special definitions.
            - power_per_photon: Power per photon (float).
    """
    with open(ascii_file, 'r') as f:
        lines = f.readlines()

    # Extract parameters
    start_params = lines.index("START PARAMETERS\n") + 1
    end_params = lines.index("END PARAMETERS\n")
    parameter_names = [line.strip() for line in lines[start_params:end_params]]

    # Extract surfaces
    start_surfaces = lines.index("START SURFACES\n") + 1
    end_surfaces = lines.index("END SURFACES\n")
    surfaces = {}
    for line in lines[start_surfaces:end_surfaces]:
        parts = line.split("//")
        surface_id = parts[0].strip()
        if surface_id == "1 /Sun":
            surfaces[1] = "Sun (Virtual Surface)"  # Special mapping for the Sun
        else:
            try:
                surface_id = int(surface_id)  # Convert to integer for physical surfaces
                surface_url = parts[1].strip() if len(parts) > 1 else "Unknown"
                surfaces[surface_id] = surface_url
            except (ValueError, IndexError):
                print(f"Warning: Skipping invalid surface definition: {line.strip()}")

    # Extract power per photon
    power_per_photon = float(lines[-1].strip())

    return parameter_names, surfaces, power_per_photon

def process_binary_file_sequential(file_path, num_parameters):
    """
    Processes a single binary file to build ray trajectories sequentially.

    Args:
        file_path (str): Path to the binary file.
        num_parameters (int): Number of parameters per photon.

    Returns:
        list: List of ray trajectories. Each trajectory is a list of photon records.
    """
    photons = np.fromfile(file_path, dtype=">f8").reshape(-1, num_parameters)
    photon_dict = {int(photon[0]): photon for photon in photons}  # Map photon IDs to photon records

    # Build ray trajectories
    trajectories = []
    for photon in photons:
        if int(photon[5]) == 0:  # Start of a trajectory (previous ID = 0)
            trajectory = []
            current_id = int(photon[0])
            while current_id != 0:
                trajectory.append(photon_dict[current_id])
                current_id = int(photon_dict[current_id][6]) if current_id in photon_dict else 0
            trajectories.append(trajectory)
    
    return trajectories


def consolidate_trajectories(all_trajectories):
    """
    Consolidates ray trajectories across multiple files.

    Args:
        all_trajectories (list): List of ray trajectories from all files.

    Returns:
        list: Consolidated ray trajectories.
    """
    trajectory_map = {}  # Map of trajectory start ID to trajectory

    for trajectory in all_trajectories:
        start_id = int(trajectory[0][0])  # Use the ID of the first photon in the trajectory
        if start_id in trajectory_map:
            raise ValueError(f"Duplicate trajectory start ID found: {start_id}")
        trajectory_map[start_id] = trajectory

    # Consolidate overlapping trajectories
    consolidated = []
    visited = set()

    for trajectory in trajectory_map.values():
        if int(trajectory[0][0]) in visited:  # Skip already consolidated trajectories
            continue

        consolidated_trajectory = trajectory
        visited.add(int(trajectory[0][0]))

        # Check for continuation of the trajectory
        while True:
            next_id = int(consolidated_trajectory[-1][6])  # Next ID of the last photon
            if next_id == 0 or next_id not in trajectory_map:
                break
            consolidated_trajectory += trajectory_map[next_id]
            visited.add(next_id)

        consolidated.append(consolidated_trajectory)

    return consolidated


def filter_relevant_trajectories(trajectories, surface_id):
    """
    Filters and extracts relevant photons from trajectories.

    Args:
        trajectories (list): List of ray trajectories.
        surface_id (int): Surface ID of interest.

    Returns:
        np.ndarray: Array of filtered photon records.
    """
    relevant_photons = []

    for trajectory in trajectories:
        # Skip trajectories with no length
        if len(trajectory) < 2:
            continue

        # Check if any photon in the trajectory is on the surface of interest
        surface_photons = [p for p in trajectory if int(p[-1]) == surface_id]
        if not surface_photons:
            continue

        # Extract the surface photon and its previous photon
        surface_photon = surface_photons[0]
        previous_id = int(surface_photon[5])
        previous_photon = next((p for p in trajectory if int(p[0]) == previous_id), None)

        if previous_photon is not None:
            relevant_photons.append(previous_photon)
        relevant_photons.append(surface_photon)

    return np.array(relevant_photons)


def process_binary_files_sequential(binary_files, num_parameters, surface_id):
    """
    Processes all binary files sequentially and consolidates trajectories.

    Args:
        binary_files (list): List of binary file paths.
        num_parameters (int): Number of parameters per photon.
        surface_id (int): Surface ID of interest.

    Returns:
        np.ndarray: Array of relevant photon records.
    """
    all_trajectories = []

    # Process each binary file
    for file_path in binary_files:
        file_trajectories = process_binary_file_sequential(file_path, num_parameters)
        all_trajectories.extend(file_trajectories)

    # Consolidate trajectories across files
    consolidated_trajectories = consolidate_trajectories(all_trajectories)

    # Filter relevant photons
    relevant_photons = filter_relevant_trajectories(consolidated_trajectories, surface_id)

    return relevant_photons
