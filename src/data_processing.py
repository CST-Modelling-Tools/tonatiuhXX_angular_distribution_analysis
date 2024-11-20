import numpy as np
import os
import re
from multiprocessing import Pool

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

def process_binary_file(args):
    """
    Processes a single binary file to filter relevant photons.

    Args:
        args (tuple): (file_path, num_parameters, surface_id, chunk_size)

    Returns:
        tuple: (relevant_photons, previous_ids)
            - relevant_photons: Photons hitting the specified surface.
            - previous_ids: Set of previous IDs collected.
    """
    file_path, num_parameters, surface_id, chunk_size = args
    relevant_photons = []
    previous_ids = set()

    with open(file_path, "rb") as f:
        while True:
            # Read a chunk of data
            chunk = np.fromfile(f, dtype=">f8", count=chunk_size * num_parameters)
            if chunk.size == 0:
                break  # End of file

            # Reshape into photon records
            chunk = chunk.reshape(-1, num_parameters)

            # Filter photons hitting the specified surface
            photons_on_surface = chunk[chunk[:, -1] == surface_id]
            relevant_photons.append(photons_on_surface)

            # Collect previous IDs for further filtering
            previous_ids.update(photons_on_surface[:, 5][photons_on_surface[:, 5] != 0])

    # Combine all relevant photons into a single array
    relevant_photons = np.vstack(relevant_photons) if relevant_photons else np.empty((0, num_parameters))
    return relevant_photons, previous_ids


def combine_results(results, binary_files, num_parameters):
    """
    Combines results from all parallel processes and ensures all previous IDs are processed.

    Args:
        results (list): List of (relevant_photons, previous_ids) tuples from processes.
        binary_files (list): List of binary files for reprocessing previous IDs.
        num_parameters (int): Number of parameters per photon.

    Returns:
        np.ndarray: Combined and deduplicated photon records.
    """
    all_photons = []
    all_previous_ids = set()

    # Combine photons and collect previous IDs
    for photons, previous_ids in results:
        all_photons.append(photons)
        all_previous_ids.update(previous_ids)

    # Combine all photon records
    combined_photons = np.vstack(all_photons)

    # Process previous photons
    previous_photons = []
    if all_previous_ids:
        for binary_file in binary_files:
            with open(binary_file, "rb") as f:
                all_photons_in_file = np.fromfile(f, dtype=">f8").reshape(-1, num_parameters)
                for pid in all_previous_ids:
                    matching_photon = all_photons_in_file[all_photons_in_file[:, 0] == pid]
                    if len(matching_photon) > 0:
                        previous_photons.append(matching_photon[0])

    # Add previous photons to combined data
    if previous_photons:
        combined_photons = np.vstack((combined_photons, np.array(previous_photons)))

    # Deduplicate photons (ensure unique photon IDs)
    _, unique_indices = np.unique(combined_photons[:, 0], return_index=True)
    combined_photons = combined_photons[unique_indices]

    return combined_photons


def parallel_filter_photons(binary_files, num_parameters, surface_id, chunk_size=10_000, num_workers=4):
    """
    Filters photons in parallel across multiple binary files.

    Args:
        binary_files (list): List of binary file paths.
        num_parameters (int): Number of parameters per photon.
        surface_id (int): Surface ID of interest.
        chunk_size (int): Number of photons to read per chunk.
        num_workers (int): Number of parallel workers.

    Returns:
        np.ndarray: Array of relevant photon records.
    """
    # Prepare arguments for each binary file
    args = [(file, num_parameters, surface_id, chunk_size) for file in binary_files]

    # Use a multiprocessing pool to process files in parallel
    with Pool(processes=num_workers) as pool:
        results = pool.map(process_binary_file, args)

    # Combine results from all processes
    combined_photons = combine_results(results, binary_files, num_parameters)

    return combined_photons


if __name__ == "__main__":
    ascii_file = "data/photons_parameters.txt"
    binary_dir = "data"
    surface_id = 7  # Specify the surface ID of interest

    # Parse the ASCII file to get parameter information
    parameter_names, surfaces, power_per_photon = parse_ascii_file(ascii_file)
    num_parameters = len(parameter_names)

    # Detect binary files
    binary_files = sorted(
        [os.path.join(binary_dir, f) for f in os.listdir(binary_dir) if re.match(r"photons.*\.dat", f)]
    )

    # Perform parallel filtering
    num_workers = os.cpu_count()  # Use all available cores
    filtered_photon_records = parallel_filter_photons(binary_files, num_parameters, surface_id, num_workers=num_workers)

    # Display results
    print(f"Number of relevant photons: {len(filtered_photon_records)}")

    formatted_record = np.array2string(filtered_photon_records[0], formatter={'float_kind': lambda x: f"{x:.2f}"})
    print(f"Example Photon Record: {formatted_record}")
