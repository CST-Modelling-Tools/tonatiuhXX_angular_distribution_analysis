import numpy as np
import os
import re


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


def filter_relevant_photons(binary_files, num_parameters, surface_id, chunk_size=10_000):
    """
    Filters relevant photons while reading binary files:
    1. Photons hitting the specified surface.
    2. Their corresponding "previous photons."

    Args:
        binary_files (list): List of binary file paths.
        num_parameters (int): Number of parameters per photon.
        surface_id (int): Surface ID of interest.
        chunk_size (int): Number of photons to read per chunk.

    Returns:
        np.ndarray: Array of relevant photon records.
    """
    relevant_photons = []
    previous_ids = set()

    for binary_file in binary_files:
        with open(binary_file, "rb") as f:
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

    # Include photons corresponding to "previous IDs"
    if previous_ids:
        for binary_file in binary_files:
            with open(binary_file, "rb") as f:
                all_photons = np.fromfile(f, dtype=">f8").reshape(-1, num_parameters)
                previous_photons = np.array([all_photons[all_photons[:, 0] == pid][0]
                                             for pid in previous_ids if np.any(all_photons[:, 0] == pid)])
                relevant_photons = np.vstack((relevant_photons, previous_photons))

    # Deduplicate photons (ensure unique photon IDs)
    _, unique_indices = np.unique(relevant_photons[:, 0], return_index=True)
    relevant_photons = relevant_photons[unique_indices]

    return relevant_photons


def main(ascii_file, binary_dir, surface_id):
    """
    Main function to process photon data while filtering for relevant photons.
    Args:
        ascii_file (str): Path to the ASCII file.
        binary_dir (str): Directory containing the binary files.
        surface_id (int): Surface ID of interest.

    Returns:
        tuple: (photon_records, parameter_names, surfaces, power_per_photon)
    """
    # Parse the ASCII file
    parameter_names, surfaces, power_per_photon = parse_ascii_file(ascii_file)

    # Detect binary files
    binary_files = sorted(
        [os.path.join(binary_dir, f) for f in os.listdir(binary_dir) if re.match(r"photons.*\.dat", f)]
    )

    # Get the number of parameters per photon
    num_parameters = len(parameter_names)

    # Filter relevant photons
    photon_records = filter_relevant_photons(binary_files, num_parameters, surface_id)

    return photon_records, parameter_names, surfaces, power_per_photon


if __name__ == "__main__":
    ascii_file = "data/photons_parameters.txt"
    binary_dir = "data"
    surface_id = 7  # Specify the surface ID of interest

    # Process files and filter relevant photons
    photon_records, parameter_names, surfaces, power_per_photon = main(ascii_file, binary_dir, surface_id)

    # Display results
    print(f"Parameter Names: {parameter_names}")
    # print(f"Surfaces: {surfaces}")
    print(f"Power per Photon: {power_per_photon} W")
    print(f"Total Relevant Photon Records: {len(photon_records)}")

    formatted_record = np.array2string(photon_records[0], formatter={'float_kind': lambda x: f"{x:.2f}"})
    print(f"Example Photon Record: {formatted_record}")
