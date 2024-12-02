import csv
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Function to read data from results.csv
def read_csv(file_path):
    points = []
    lengths = []
    
    with open(file_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # Skip the header
        for row in reader:
            # Extract PointA (x, y, z) and the length
            x, y, z = map(float, row[:3])
            length = abs(float(row[6]))  # Length is assumed to be in the 7th column (index 6)
            points.append((x, y, z))
            lengths.append(length)
    
    return np.array(points), np.array(lengths)

# Function to plot the 3D points
def plot_3d_points(points, lengths):
    x, y, z = points[:, 0], points[:, 1], points[:, 2]

    # Create a 3D plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Scatter plot with colors based on lengths
    scatter = ax.scatter(x, y, z, c=lengths, cmap='viridis', s=10)
    fig.colorbar(scatter, ax=ax, label='Length |PointB - PointA|')

    # Set labels
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('3D Visualization of PointsA Colored by Vector Length')

    plt.show()

# Main script
if __name__ == "__main__":
    # Path to the CSV file
    file_path = "C:/Users/manue_6t240gh/Dropbox/OpenSource/angular_distribution/data/results.csv"

    # Read data from the CSV file
    points, lengths = read_csv(file_path)

    # Plot the data in 3D
    plot_3d_points(points, lengths)
