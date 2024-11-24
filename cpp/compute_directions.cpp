#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <array>
#include <cmath>
#include <vector>

namespace py = pybind11;

// Helper function to compute the norm of a vector
double vector_norm(const std::array<double, 3>& vec) {
    return std::sqrt(vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2]);
}

// Spherical to Cartesian conversion
std::array<double, 3> spherical_to_cartesian(double azimuth, double elevation) {
    double azimuth_rad = azimuth * M_PI / 180.0;
    double elevation_rad = elevation * M_PI / 180.0;

    double x = std::cos(elevation_rad) * std::sin(azimuth_rad);
    double y = std::cos(elevation_rad) * std::cos(azimuth_rad);
    double z = std::sin(elevation_rad);

    return {x, y, z};
}

// Compute normalized direction vectors
py::array_t<double> compute_directions(const py::array_t<double>& photon_records) {
    auto records = photon_records.unchecked<2>();
    py::ssize_t num_records = records.shape(0);

    // Create a vector to store non-zero direction vectors
    std::vector<std::array<double, 3>> valid_directions;

    for (py::ssize_t i = 0; i < num_records; ++i) {
        int previous_id = static_cast<int>(records(i, 5));
        if (previous_id == 0) continue;

        std::array<double, 3> direction_vector = {0.0, 0.0, 0.0};

        // Find the record with the previous photon ID
        for (py::ssize_t j = 0; j < num_records; ++j) {
            if (static_cast<int>(records(j, 0)) == previous_id) {
                direction_vector = {
                    records(j, 1) - records(i, 1),
                    records(j, 2) - records(i, 2),
                    records(j, 3) - records(i, 3),
                };
                break;
            }
        }

        // Normalize the direction vector
        double magnitude = vector_norm(direction_vector);
        if (magnitude > 0) {
            direction_vector[0] /= magnitude;
            direction_vector[1] /= magnitude;
            direction_vector[2] /= magnitude;
            valid_directions.push_back(direction_vector);
        }
    }

    // Create NumPy array with the shape (num_directions, 3)
    py::ssize_t num_directions = valid_directions.size();
    py::array_t<double> result(py::array::ShapeContainer(std::vector<py::ssize_t>{num_directions, 3}));

    auto result_ptr = result.mutable_data();

    // Copy the data into the result array
    for (py::ssize_t i = 0; i < num_directions; ++i) {
        result_ptr[i * 3 + 0] = valid_directions[i][0];
        result_ptr[i * 3 + 1] = valid_directions[i][1];
        result_ptr[i * 3 + 2] = valid_directions[i][2];
    }

    return result;
}


// Transform to local coordinate system
py::array_t<double> transform_to_local(const py::array_t<double>& directions,
                                       const std::array<double, 3>& local_x,
                                       const std::array<double, 3>& local_y,
                                       const std::array<double, 3>& local_z) {
    auto dirs = directions.unchecked<2>();
    py::ssize_t num_directions = dirs.shape(0);

    py::array_t<double> local_directions(py::array::ShapeContainer({num_directions, 3}));
    auto local_ptr = local_directions.mutable_data();

    for (py::ssize_t i = 0; i < num_directions; ++i) {
        for (int j = 0; j < 3; ++j) {
            local_ptr[i * 3 + j] = dirs(i, 0) * local_x[j] + dirs(i, 1) * local_y[j] + dirs(i, 2) * local_z[j];
        }
    }

    return local_directions;
}

// Bind functions to Python
PYBIND11_MODULE(compute_directions, m) {
    m.def("compute_directions", &compute_directions, "Compute normalized direction vectors");
    m.def("transform_to_local", &transform_to_local, "Transform to local coordinate system");
    m.def("spherical_to_cartesian", &spherical_to_cartesian, "Convert spherical to Cartesian coordinates");
}
