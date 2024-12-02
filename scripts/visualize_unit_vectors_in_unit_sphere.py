import csv
import numpy as np
import pyvista as pv

print(pv.__version__)

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

# Main script
if __name__ == "__main__":
# Path to the CSV file
    file_path = "C:/Users/manue_6t240gh/Dropbox/OpenSource/angular_distribution/data/results.csv"

    # Read data from the CSV file
    unit_vectors, lengths = read_csv(file_path)

    # Extract coordinates of unit vector ends
    x, y, z = unit_vectors[:, 0], unit_vectors[:, 1], unit_vectors[:, 2]

    # Create a PyVista plotter
    plotter = pv.Plotter()

    # Add the unit sphere
    sphere = pv.Sphere(radius=1)
    plotter.add_mesh(
        sphere, color="lightgray", opacity=0.3, style="wireframe", label="Unit Sphere"
    )

    # Add the points representing the unit vector ends
    points = np.column_stack((x, y, z))
    point_cloud = pv.PolyData(points)
    plotter.add_mesh(
        point_cloud,
        scalars=lengths,  # Use lengths to color the points
        cmap="viridis",   # Colormap
        point_size=2,    # Adjust point size
        render_points_as_spheres=True,
    )

    # Add labels and adjust view
    plotter.add_axes(interactive=True)
    plotter.set_background("white")
    plotter.show_bounds(grid="front", location="outer", ticks="both")
    plotter.view_isometric()

    # Show the plot
    plotter.show()
