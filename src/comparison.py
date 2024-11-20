import numpy as np
import os
import re
import time
from multiprocessing import Pool


# Shared Function: Parse ASCII File
def parse_ascii_file(ascii_file):
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
            surfaces[1] = "Sun (Virtual Surface)"
        else:
            try:
                surface_id = int(surface_id)
                surface_url = parts[1].strip() if len(parts) > 1 else "Unknown"
                surfaces[surface_id] = surface_url
            except (ValueError, IndexError):
                print(f"Warning: Skipping invalid surface definition: {line.strip()}")

    # Extract power per photon
    power_per_photon = float(lines[-1].strip())

    return parameter_names, surfaces, power_per_photon


# Serial Version
def filter_photons_serial(binary_files, num_parameters, surface_id):
    photon_records = []
    previous_ids = set()

    for binary_file in binary_files:
        with open(binary_file, "rb") as f:
            all_data = np.fromfile(f, dtype=">f8")
            all_photons = all_data.reshape(-1, num_parameters)

            # Filter photons hitting the specified surface
            photons_on_surface = all_photons[all_photons[:, -1] == surface_id]
            photon_records.append(photons_on_surface)

            # Collect previous IDs
            previous_ids.update(photons_on_surface[:, 5][photons_on_surface[:, 5] != 0])

    # Combine photon records
    photon_records = np.vstack(photon_records)

    # Process previous IDs
    if previous_ids:
        for binary_file in binary_files:
            with open(binary_file, "rb") as f:
                all_data = np.fromfile(f, dtype=">f8")
                all_photons = all_data.reshape(-1, num_parameters)
                previous_photons = [
                    all_photons[all_photons[:, 0] == pid][0]
                    for pid in previous_ids if np.any(all_photons[:, 0] == pid)
                ]
                if previous_photons:
                    photon_records = np.vstack((photon_records, previous_photons))

    # Deduplicate by photon ID
    _, unique_indices = np.unique(photon_records[:, 0], return_index=True)
    return photon_records[unique_indices]


# Parallel Version
def process_binary_file(args):
    file_path, num_parameters, surface_id, chunk_size = args
    relevant_photons = []
    previous_ids = set()

    with open(file_path, "rb") as f:
        while True:
            chunk = np.fromfile(f, dtype=">f8", count=chunk_size * num_parameters)
            if chunk.size == 0:
                break
            chunk = chunk.reshape(-1, num_parameters)

            # Filter photons hitting the specified surface
            photons_on_surface = chunk[chunk[:, -1] == surface_id]
            relevant_photons.append(photons_on_surface)
            previous_ids.update(photons_on_surface[:, 5][photons_on_surface[:, 5] != 0])

    relevant_photons = np.vstack(relevant_photons) if relevant_photons else np.empty((0, num_parameters))
    return relevant_photons, previous_ids


def combine_results(results, binary_files, num_parameters):
    all_photons = []
    all_previous_ids = set()

    for photons, previous_ids in results:
        all_photons.append(photons)
        all_previous_ids.update(previous_ids)

    combined_photons = np.vstack(all_photons)

    # Add previous photons
    if all_previous_ids:
        for binary_file in binary_files:
            with open(binary_file, "rb") as f:
                all_data = np.fromfile(f, dtype=">f8")
                all_photons = all_data.reshape(-1, num_parameters)
                previous_photons = [
                    all_photons[all_photons[:, 0] == pid][0]
                    for pid in all_previous_ids if np.any(all_photons[:, 0] == pid)
                ]
                if previous_photons:
                    combined_photons = np.vstack((combined_photons, previous_photons))

    # Deduplicate
    _, unique_indices = np.unique(combined_photons[:, 0], return_index=True)
    return combined_photons[unique_indices]


def filter_photons_parallel(binary_files, num_parameters, surface_id, chunk_size=10_000, num_workers=4):
    args = [(file, num_parameters, surface_id, chunk_size) for file in binary_files]
    with Pool(processes=num_workers) as pool:
        results = pool.map(process_binary_file, args)
    return combine_results(results, binary_files, num_parameters)


# Comparison Script
def compare_photon_records(serial_records, parallel_records):
    serial_sorted = serial_records[np.argsort(serial_records[:, 0])]
    parallel_sorted = parallel_records[np.argsort(parallel_records[:, 0])]

    if np.array_equal(serial_sorted, parallel_sorted):
        print("✅ Serial and Parallel versions produce identical outputs!")
    else:
        print("❌ Serial and Parallel versions differ.")
        serial_ids = set(serial_sorted[:, 0])
        parallel_ids = set(parallel_sorted[:, 0])
        print(f"Missing in Parallel: {serial_ids - parallel_ids}")
        print(f"Missing in Serial: {parallel_ids - serial_ids}")


if __name__ == "__main__":
    # Setup
    ascii_file = "data/photons_parameters.txt"
    binary_dir = "data"
    surface_id = 7
    parameter_names, surfaces, power_per_photon = parse_ascii_file(ascii_file)
    num_parameters = len(parameter_names)
    binary_files = sorted([os.path.join(binary_dir, f) for f in os.listdir(binary_dir) if re.match(r"photons.*\.dat", f)])

    # Run Serial Version
    print("Running Serial Version...")
    start_time = time.time()
    serial_records = filter_photons_serial(binary_files, num_parameters, surface_id)
    serial_time = time.time() - start_time
    print(f"Serial Version: Processed {len(serial_records)} photons in {serial_time:.2f} seconds.")

    # Run Parallel Version
    print("Running Parallel Version...")
    start_time = time.time()
    num_workers = os.cpu_count()
    parallel_records = filter_photons_parallel(binary_files, num_parameters, surface_id, num_workers=num_workers)
    parallel_time = time.time() - start_time
    print(f"Parallel Version: Processed {len(parallel_records)} photons in {parallel_time:.2f} seconds.")

    # Compare Results
    compare_photon_records(serial_records, parallel_records)

    # Speedup Comparison
    print(f"Speedup: {serial_time / parallel_time:.2f}x")
