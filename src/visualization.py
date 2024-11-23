import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap, LinearSegmentedColormap
from scipy.spatial import ConvexHull

def plot_angular_distribution(angular_deviations, power_per_photon, bins=10, output_file="angular_distribution_power.png"):
    """
    Plots the angular distribution of photon angular deviations weighted by power.

    Args:
        angular_deviations (np.ndarray): Array of angular deviations in degrees.
        power_per_photon (float): Power associated with each photon in Watts.
        bins (int): Number of bins for the histogram.
        output_file (str): Path to save the plot.
    """
    # Calculate the histogram data
    counts, bin_edges = np.histogram(angular_deviations, bins=bins)
    power_bins = counts * power_per_photon  # Calculate power per bin

    # Plot the histogram
    plt.figure(figsize=(8, 6))
    plt.bar(
        bin_edges[:-1],
        power_bins,
        width=np.diff(bin_edges),
        color='blue',
        alpha=0.7,
        align='edge',
    )
    plt.title("Angular Distribution of Incoming Power")
    plt.xlabel("Angular Deviation (degrees)")
    plt.ylabel("Power (W)")
    plt.grid()
    plt.savefig(output_file)
    print(f"Plot saved to {output_file}")
    plt.show(block=False)  # Allow multiple figures


def plot_polar_distribution_of_rays_with_hull(directions, output_file="plot_polar_distribution_of_rays_with_hull.png"):
    """
    Plots the polar distribution of direction vectors and overlays the limiting area enclosing all rays.

    Args:
        directions (np.ndarray): Array of normalized direction vectors (shape: [N, 3]).
        output_file (str): Path to save the plot.
    """
    # Convert directions to polar coordinates
    azimuth = np.arctan2(directions[:, 0], directions[:, 1])  # Azimuth in radians
    zenith = np.degrees(np.arccos(directions[:, 2]))  # Zenith in degrees

    # Convert to Cartesian for Convex Hull calculation
    x = zenith * np.cos(azimuth)
    y = zenith * np.sin(azimuth)

    # Compute Convex Hull
    points = np.vstack((x, y)).T
    hull = ConvexHull(points)

    # Plot polar distribution
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(10, 8))
    ax.scatter(azimuth, zenith, c='blue', alpha=0.7, s=1, label="Photon Directions")

    # Plot Convex Hull
    hull_points = points[hull.vertices]
    hull_azimuth = np.arctan2(hull_points[:, 1], hull_points[:, 0])
    hull_zenith = np.sqrt(hull_points[:, 0]**2 + hull_points[:, 1]**2)
    hull_azimuth = np.append(hull_azimuth, hull_azimuth[0])  # Close the loop
    hull_zenith = np.append(hull_zenith, hull_zenith[0])

    ax.plot(hull_azimuth, hull_zenith, color='red', lw=2, label="Enclosing Boundary")

    # Set plot aesthetics
    ax.set_ylim(0, 90)
    ax.set_title("Distribution of Incoming Rays Around Aperture Normal", fontsize=16)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.legend(loc="upper right")
    plt.savefig(output_file)
    print(f"Plot saved to {output_file}")
    plt.show(block=False)

def plot_polar_power_distribution_with_hull(directions, power_per_photon, bins=30, output_file="polar_power_distribution_with_hull.png"):
    """
    Plots the power density distribution in polar coordinates, normalizing by solid angle,
    and overlays the convex hull enclosing all rays.

    Args:
        directions (np.ndarray): Array of normalized direction vectors (shape: [N, 3]).
        power_per_photon (float): Power per photon in Watts.
        bins (int): Number of bins for azimuth and zenith angles.
        output_file (str): Path to save the plot.
    """
    # Convert Cartesian directions to spherical coordinates
    azimuth = np.arctan2(directions[:, 0], directions[:, 1])  # Azimuth in radians
    zenith = np.degrees(np.arccos(directions[:, 2]))          # Zenith in degrees

    # Define bin edges for azimuth and zenith
    azimuth_edges = np.linspace(-np.pi, np.pi, bins + 1)  # Azimuth bins in radians
    zenith_edges = np.linspace(0, 90, bins + 1)           # Zenith bins in degrees

    # Bin data into a 2D histogram
    power_density, _, _ = np.histogram2d(
        azimuth, zenith, bins=[azimuth_edges, zenith_edges], weights=np.full_like(azimuth, power_per_photon)
    )

    # Compute bin area using solid angle formula
    zenith_centers = (zenith_edges[:-1] + zenith_edges[1:]) / 2  # Midpoints in degrees
    sin_zenith = np.sin(np.radians(zenith_centers))  # sin(zenith) for bin centers
    bin_area = np.outer(sin_zenith, np.diff(azimuth_edges)) * np.diff(np.radians(zenith_edges))  # Solid angle

    bin_area[bin_area <= 0] = np.inf  # Prevent division by zero or negative areas

    # Normalize power density by solid angle (bin area)
    power_density_per_sr = np.divide(
        power_density, bin_area.T,
        out=np.zeros_like(power_density), where=bin_area.T > 0
    )

    # Convert to MW/sr for display but keep calculations in W/sr
    power_density_per_sr_mw = power_density_per_sr / 1e6

    # Print debugging info
    print(f"Min Radiance (MW/sr): {np.min(power_density_per_sr_mw)}")
    print(f"Max Radiance (MW/sr): {np.max(power_density_per_sr_mw)}")

    # Set colormap range in W/sr
    vmin = 0
    vmax = 7e6  # 7 MW/sr converted to W/sr

    # Create a custom colormap with transitions at 0, 2.33, 4.66, and 7 MW/sr
    colors = [
        (1.0, 1.0, 1.0),  # White at 0
        (0.0, 0.0, 0.5),  # Dark blue at 2.33 MW/sr
        (1.0, 0.9, 0.0),  # Dark yellow at 4.66 MW/sr
        (0.8, 0.0, 0.0),  # Dark red at 7 MW/sr
    ]
    radiance_cmap = LinearSegmentedColormap.from_list("CustomRadiance", colors, N=256)

    # Convert edges to centers
    azimuth_centers = (azimuth_edges[:-1] + azimuth_edges[1:]) / 2
    zenith_centers = (zenith_edges[:-1] + zenith_edges[1:]) / 2

    # Create a meshgrid for plotting
    theta, r = np.meshgrid(azimuth_centers, zenith_centers)

    # Calculate Convex Hull
    x = zenith * np.cos(azimuth)
    y = zenith * np.sin(azimuth)
    points = np.vstack((x, y)).T
    hull = ConvexHull(points)
    hull_points = points[hull.vertices]
    hull_azimuth = np.arctan2(hull_points[:, 1], hull_points[:, 0])
    hull_zenith = np.sqrt(hull_points[:, 0]**2 + hull_points[:, 1]**2)
    hull_azimuth = np.append(hull_azimuth, hull_azimuth[0])  # Close the loop
    hull_zenith = np.append(hull_zenith, hull_zenith[0])

    # Plot the histogram as a heatmap
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(10, 8))
    heatmap = ax.pcolormesh(
        theta, r, power_density_per_sr.T, cmap=radiance_cmap, shading='auto', vmin=vmin, vmax=vmax
    )
    cbar = plt.colorbar(heatmap, ax=ax, pad=0.1)
    cbar.set_label("Power Density (W/sr)")

    # Plot Convex Hull
    ax.plot(hull_azimuth, hull_zenith, color='red', lw=2, label="Enclosing Boundary")

    # Customize plot appearance
    ax.set_title("Power Density Distribution with Convex Hull (MW/sr)", fontsize=16)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 90)  # Zenith angle range (degrees)
    ax.set_rticks([10, 20, 30, 40, 50, 60, 70, 80, 90])  # Set radial ticks
    ax.set_rlabel_position(0)  # Move radial labels to avoid overlap with grid lines
    ax.legend(loc="upper right")

    # Save and show the plot
    plt.savefig(output_file, dpi=300)
    print(f"Plot saved to {output_file}")
    plt.show(block=False)

def plot_power_azimuth(directions, power_per_photon, bins=30, output_file="power_azimuth.png"):
    """
    Plots both power and cumulative power distribution as a function of azimuth angle.

    Args:
        directions (np.ndarray): Array of normalized direction vectors (shape: [N, 3]).
        power_per_photon (float): Power associated with each photon in Watts.
        bins (int): Number of bins for azimuth angles.
        output_file (str): Path to save the plot.
    """
    # Convert Cartesian directions to azimuth in radians
    azimuth = np.arctan2(directions[:, 0], directions[:, 1])  # Azimuth in radians
    azimuth = np.degrees(azimuth)  # Convert to degrees
    azimuth = (azimuth + 360) % 360  # Map range to [0, 360)

    # Define azimuth bin edges
    azimuth_edges = np.linspace(0, 360, bins + 1)  # Azimuth bins in degrees

    # Compute energy per azimuth bin
    energy_per_bin, _ = np.histogram(azimuth, bins=azimuth_edges, weights=np.full_like(azimuth, power_per_photon))

    # Compute cumulative energy
    cumulative_energy = np.cumsum(energy_per_bin)

    # Azimuth bin centers
    azimuth_centers = (azimuth_edges[:-1] + azimuth_edges[1:]) / 2

    # Plot both cumulative energy and power vs. azimuth
    fig, ax1 = plt.subplots(figsize=(8, 6))

    # Plot Power vs. Azimuth
    ax1.bar(azimuth_centers, energy_per_bin, width=(360 / bins), color='blue', alpha=0.5, label='Power vs. Azimuth')
    ax1.set_xlabel("Azimuth (degrees)")
    ax1.set_ylabel("Power (W)", color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # Plot Cumulative Energy vs. Azimuth on the same axis
    ax2 = ax1.twinx()
    ax2.plot(azimuth_centers, cumulative_energy, marker='o', color='red', alpha=0.8, label='Cumulative Energy')
    ax2.set_ylabel("Cumulative Power (W)", color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    # Add titles and grid
    plt.title("Power and Cumulative Power vs. Azimuth")
    fig.tight_layout()
    ax1.grid()

    # Save and display the plot
    plt.savefig(output_file)
    print(f"Plot saved to {output_file}")
    plt.show(block=False)

def plot_power_zenith(directions, power_per_photon, bins=30, output_file="power_zenith.png"):
    """
    Plots both power and cumulative power distribution as a function of zenith angle.

    Args:
        directions (np.ndarray): Array of normalized direction vectors (shape: [N, 3]).
        power_per_photon (float): Power associated with each photon in Watts.
        bins (int): Number of bins for zenith angles.
        output_file (str): Path to save the plot.
    """
    # Convert Cartesian directions to zenith in degrees
    zenith = np.degrees(np.arccos(directions[:, 2]))  # Zenith in degrees

    # Define zenith bin edges
    zenith_edges = np.linspace(0, 90, bins + 1)  # Zenith bins from 0 to 90 degrees

    # Compute power per zenith bin
    power_per_bin, _ = np.histogram(zenith, bins=zenith_edges, weights=np.full_like(zenith, power_per_photon))

    # Compute cumulative power
    cumulative_power = np.cumsum(power_per_bin)

    # Zenith bin centers
    zenith_centers = (zenith_edges[:-1] + zenith_edges[1:]) / 2

    # Plot both cumulative power and power vs. zenith
    fig, ax1 = plt.subplots(figsize=(8, 6))

    # Plot Power vs. Zenith
    ax1.bar(zenith_centers, power_per_bin, width=(90 / bins), color='blue', alpha=0.5, label='Power vs. Zenith')
    ax1.set_xlabel("Zenith Angle (degrees)")
    ax1.set_ylabel("Power (W)", color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # Plot Cumulative Power vs. Zenith on the same axis
    ax2 = ax1.twinx()
    ax2.plot(zenith_centers, cumulative_power, marker='o', color='red', alpha=0.8, label='Cumulative Power')
    ax2.set_ylabel("Cumulative Power (W)", color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    # Add titles and grid
    plt.title("Power and Cumulative Power vs. Zenith Angle")
    fig.tight_layout()
    ax1.grid()

    # Save and display the plot
    plt.savefig(output_file)
    print(f"Plot saved to {output_file}")
    plt.show(block=False)

def plot_power_zenith_asymmetric(directions, power_per_photon, bins=30, output_file="power_zenith_asymmetric.png"):
    """
    Plots power and cumulative power distribution as a function of zenith angle,
    distinguishing contributions from the left (90°–270° azimuth) and right (270°–90° azimuth) hemispheres.

    Args:
        directions (np.ndarray): Array of normalized direction vectors (shape: [N, 3]).
        power_per_photon (float): Power associated with each photon in Watts.
        bins (int): Number of bins for zenith angles.
        output_file (str): Path to save the plot.
    """
    # Convert Cartesian directions to azimuth and zenith
    azimuth = np.arctan2(directions[:, 0], directions[:, 1])  # Azimuth in radians
    azimuth = np.degrees(azimuth)  # Convert to degrees
    azimuth = (azimuth + 360) % 360  # Map azimuth to [0, 360)

    zenith = np.degrees(np.arccos(directions[:, 2]))  # Zenith in degrees

    # Define hemispheres based on azimuth
    upward_hemisphere = (azimuth >= 270) | (azimuth <= 90)  # Azimuths from 270° to 90°
    downward_hemisphere = (azimuth > 90) & (azimuth < 270)  # Azimuths from 90° to 270°

    # Define zenith bin edges
    zenith_edges = np.linspace(0, 90, bins + 1)

    # Compute power per zenith bin for each hemisphere
    power_upward, _ = np.histogram(zenith[upward_hemisphere], bins=zenith_edges, weights=np.full_like(zenith[upward_hemisphere], power_per_photon))
    power_downward, _ = np.histogram(zenith[downward_hemisphere], bins=zenith_edges, weights=np.full_like(zenith[downward_hemisphere], power_per_photon))

    # Compute cumulative power for each hemisphere
    cumulative_power_upward = np.cumsum(power_upward)
    cumulative_power_downward = np.cumsum(power_downward)

    # Zenith bin centers
    zenith_centers = (zenith_edges[:-1] + zenith_edges[1:]) / 2

    # Plot power and cumulative power for upward and downward hemispheres
    fig, ax1 = plt.subplots(figsize=(8, 6))

    # Plot upward hemisphere power (positive direction)
    ax1.bar(zenith_centers, power_upward, width=(90 / bins), color='blue', alpha=0.5, label='Upward Hemisphere (270°–90°)')
    # Plot downward hemisphere power (negative direction)
    ax1.bar(zenith_centers, -power_downward, width=(90 / bins), color='orange', alpha=0.5, label='Downward Hemisphere (90°–270°)')
    ax1.set_xlabel("Zenith Angle (degrees)")
    ax1.set_ylabel("Power (W)")
    ax1.legend(loc="upper left")
    ax1.grid()

    # Adjust the y-axis ticks to remove negative signs for the downward hemisphere
    yticks = ax1.get_yticks()
    ax1.set_yticklabels([f"{abs(tick):.0f}" for tick in yticks])

    # Plot cumulative power on the same axis
    ax2 = ax1.twinx()
    ax2.plot(zenith_centers, cumulative_power_upward, marker='o', color='green', alpha=0.8, label='Cumulative Upward Power')
    ax2.plot(zenith_centers, -cumulative_power_downward, marker='o', color='red', alpha=0.8, label='Cumulative Downward Power')
    ax2.set_ylabel("Cumulative Power (W)")
    ax2.tick_params(axis='y')
    ax2.legend(loc="upper right")

    # Add titles and save the plot
    plt.title("Power and Cumulative Power vs. Zenith Angle (Upward vs. Downward Hemispheres)")
    fig.tight_layout()
    plt.savefig(output_file)
    print(f"Plot saved to {output_file}")
    plt.show(block=False)

def plot_polar_normalized_power_distribution(directions, power_per_photon, bins=30, output_file="polar_normalized_power_distribution.png"):
    """
    Plots the non-dimensional power density distribution in polar coordinates, normalized by the maximum radiance,
    and overlays the convex hull enclosing all rays.

    Args:
        directions (np.ndarray): Array of normalized direction vectors (shape: [N, 3]).
        power_per_photon (float): Power per photon in Watts.
        bins (int): Number of bins for azimuth and zenith angles.
        output_file (str): Path to save the plot.
    """
    # Convert Cartesian directions to spherical coordinates
    azimuth = np.arctan2(directions[:, 0], directions[:, 1])  # Azimuth in radians
    zenith = np.degrees(np.arccos(directions[:, 2]))          # Zenith in degrees

    # Define bin edges for azimuth and zenith
    azimuth_edges = np.linspace(-np.pi, np.pi, bins + 1)  # Azimuth bins in radians
    zenith_edges = np.linspace(0, 90, bins + 1)           # Zenith bins in degrees

    # Bin data into a 2D histogram
    power_density, _, _ = np.histogram2d(
        azimuth, zenith, bins=[azimuth_edges, zenith_edges], weights=np.full_like(azimuth, power_per_photon)
    )

    # Compute bin area using solid angle formula
    zenith_centers = (zenith_edges[:-1] + zenith_edges[1:]) / 2  # Midpoints in degrees
    sin_zenith = np.sin(np.radians(zenith_centers))  # sin(zenith) for bin centers
    bin_area = np.outer(sin_zenith, np.diff(azimuth_edges)) * np.diff(np.radians(zenith_edges))  # Solid angle

    bin_area[bin_area <= 0] = np.inf  # Prevent division by zero or negative areas

    # Normalize power density by solid angle (bin area)
    radiance_per_sr = np.divide(
        power_density, bin_area.T,
        out=np.zeros_like(power_density), where=bin_area.T > 0
    )

    # Compute maximum radiance
    max_radiance = np.max(radiance_per_sr)
    print(f"Maximum Radiance: {max_radiance:.2f} W/sr")

    # Normalize radiance by maximum radiance
    normalized_radiance = radiance_per_sr / max_radiance

    # Create a custom colormap (white -> dark blue -> dark yellow -> dark red)
    colors = [
        (1.0, 1.0, 1.0),  # White at 0
        (0.0, 0.0, 0.5),  # Dark blue at 0.33
        (1.0, 0.9, 0.0),  # Dark yellow at 0.66
        (0.8, 0.0, 0.0),  # Dark red at 1.0
    ]
    custom_cmap = LinearSegmentedColormap.from_list("CustomRadiance", colors, N=256)

    # Convert edges to centers
    azimuth_centers = (azimuth_edges[:-1] + azimuth_edges[1:]) / 2
    zenith_centers = (zenith_edges[:-1] + zenith_edges[1:]) / 2

    # Create a meshgrid for plotting
    theta, r = np.meshgrid(azimuth_centers, zenith_centers)

    # Calculate Convex Hull
    x = zenith * np.cos(azimuth)
    y = zenith * np.sin(azimuth)
    points = np.vstack((x, y)).T
    hull = ConvexHull(points)
    hull_points = points[hull.vertices]
    hull_azimuth = np.arctan2(hull_points[:, 1], hull_points[:, 0])
    hull_zenith = np.sqrt(hull_points[:, 0]**2 + hull_points[:, 1]**2)
    hull_azimuth = np.append(hull_azimuth, hull_azimuth[0])  # Close the loop
    hull_zenith = np.append(hull_zenith, hull_zenith[0])

    # Plot the histogram as a heatmap
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(10, 8))
    heatmap = ax.pcolormesh(
        theta, r, normalized_radiance.T, cmap=custom_cmap, shading='auto', vmin=0, vmax=1.0
    )
    cbar = plt.colorbar(heatmap, ax=ax, pad=0.1)
    cbar.set_label("Non-Dimensional Radiance")

    # Plot Convex Hull
    ax.plot(hull_azimuth, hull_zenith, color='red', lw=2, label="Enclosing Boundary")

    # Customize plot appearance
    ax.set_title("Non-Dimensional Power Density Distribution", fontsize=16)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 90)  # Zenith angle range (degrees)
    ax.set_rticks([10, 20, 30, 40, 50, 60, 70, 80, 90])  # Set radial ticks
    ax.set_rlabel_position(0)  # Move radial labels to avoid overlap with grid lines
    ax.legend(loc="upper right")

    # Add the maximum radiance to the plot
    ax.text(0.5, 1.1, f"Max Radiance: {max_radiance / 1e6:.2f} MW/sr", transform=ax.transAxes, fontsize=12, ha="center")


    # Save and show the plot
    plt.savefig(output_file, dpi=300)
    print(f"Plot saved to {output_file}")
    plt.show(block=False)