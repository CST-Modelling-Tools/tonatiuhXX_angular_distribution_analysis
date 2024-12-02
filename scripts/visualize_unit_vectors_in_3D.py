import csv
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Function to read data from results.csv
def read_csv(file_path):
    unit_vectors = []
    lengths = []
    
    with open(file_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # Skip the header
        for row in reader:
            # Extract unit vector components and the length
            ux, uy, uz = map(float, row[3:6])  # Unit vector components
            length = abs(float(row[6]))  # Length is in the 7th column (index 6)
            unit_vectors.append((ux, uy, uz))
            lengths.append(length)
    
    return np.array(unit_vectors), np.array(lengths)

# Function to plot 3D unit vectors from the origin
def plot_unit_vectors_from_origin(unit_vectors, lengths):

    # Extract coordinates
    x_end, y_end, z_end =     end_points = unit_vectors[:, 0], unit_vectors[:, 1], unit_vectors[:, 2]

    # Create a 3D plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Plot the unit vector endpoints
    scatter = ax.scatter(x_end, y_end, z_end, c=lengths, cmap='viridis', s=10)
    fig.colorbar(scatter, ax=ax, label='Length |PointB - PointA|')

    # Set labels
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('3D Unit Vectors from Origin Colored by Vector Length')

    plt.show()

# Main script
if __name__ == "__main__":
    # Path to the CSV file
    file_path = "C:/Users/manue_6t240gh/Dropbox/OpenSource/angular_distribution/data/results.csv"

    # Read data from the CSV file
    unit_vectors, lengths = read_csv(file_path)

    # Plot the unit vector endpoints
    plot_unit_vectors_from_origin(unit_vectors, lengths)
