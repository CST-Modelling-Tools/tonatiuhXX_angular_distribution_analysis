import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import ConvexHull

# Function to plot azimuth and zenith angle with convex hull
def plot_polar_azimuth_zenith_with_hull(csv_file, output_hull_file, point_size=1):

    # Read the CSV file
    data = pd.read_csv(csv_file)

    # Extract the data
    azimuth = np.deg2rad(data['Azimuth'])  # Convert azimuth to radians
    zenith = data['Elevation']            # Treat elevation as zenith angle
    lengths = data['Length']              # Length of the direction vector

    # Convert polar coordinates to Cartesian for Convex Hull calculation
    x = zenith * np.cos(azimuth)
    y = zenith * np.sin(azimuth)
    points = np.vstack((x, y)).T

    # Calculate the convex hull
    hull = ConvexHull(points)

    # Create the polar plot
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))
    sc = ax.scatter(azimuth, zenith, c=lengths, cmap='plasma', s=point_size, edgecolor='none')

    # Plot the convex hull
    hull_vertices = np.append(hull.vertices, hull.vertices[0])  # Close the hull
    ax.plot(azimuth[hull_vertices], zenith[hull_vertices], color='red', linewidth=1.5, label='Convex Hull')

    # Add a colorbar for the length
    cbar = plt.colorbar(sc, ax=ax, orientation='vertical')
    cbar.set_label('Ray Path Length')

    # Add grid and labels
    ax.set_theta_zero_location("N")  # Set 0° at the top
    ax.set_theta_direction(-1)       # Set azimuth direction clockwise
    ax.set_xlabel("Azimuth (degrees)", labelpad=20)
    ax.set_ylim(0, 90)               # Limit the zenith angle to [0, 90]
    ax.legend(loc='lower right')     # Add legend for convex hull

    # Add title
    plt.title('Direction of Incident Rays at the Receiver Aperture (colored by ray path length)', va='bottom')

    # Show the plot
    plt.show()

    # Extract hull coordinates in terms of azimuth and zenith
    hull_azimuth = np.rad2deg(np.arctan2(y[hull.vertices], x[hull.vertices])) % 360  # Convert back to degrees
    hull_zenith = zenith[hull.vertices]

    # Append the first element to close the hull
    hull_azimuth = np.append(hull_azimuth, hull_azimuth[:1])
    hull_zenith = np.append(hull_zenith, hull_zenith[:1])

    # Save the hull coordinates to a CSV file after plotting
    hull_data = pd.DataFrame({'Azimuth': hull_azimuth, 'Zenith': hull_zenith})
    hull_data.to_csv(output_hull_file, index=False)

# Usage example
csv_file_path = "C:/Users/manue_6t240gh/Dropbox/OpenSource/angular_distribution/data/results.csv"
hull_file_path = "C:/Users/manue_6t240gh/Dropbox/OpenSource/angular_distribution/data/convex_hull_coordinates.csv"
plot_polar_azimuth_zenith_with_hull(csv_file_path, hull_file_path, point_size=0.5)
