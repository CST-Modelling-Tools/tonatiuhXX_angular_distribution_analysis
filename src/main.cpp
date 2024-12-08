#include <iostream>
#include <fstream>
#include <chrono>
#include <vector>
#include <tuple>

#include "raypathserver.h"
#include "raypathlocalcoordinateprocessor.h"
#include "parallelprocessor.h"

int main() {
    try {
        // Input directory and surface path for processing
        std::string directoryPath = "C:/Users/manue_6t240gh/Dropbox/OpenSource/angular_distribution/data";
        std::string surfacePath = "Node/ReceiverGroup/InputAperture/InputApertureRotationX/Shape";
        std::string outputfilePath = "C:/Users/manue_6t240gh/Dropbox/OpenSource/angular_distribution/data/results.csv";

        // Initialize the RaypathServer and Processor
        RaypathServer server(directoryPath, surfacePath);
        int32_t surfaceID = server.getReferenceSurfaceID();
        double tilt = 27.0 * gcf::degree;
        vec3d surfaceCenter(0.0, 0.0, 35.0); // Replace with actual surface center coordinates
        vec3d surfaceNormal(0.0, std::cos(tilt), -std::sin(tilt)); // Replace with actual surface normal vector
        RaypathLocalCoordinateProcessor processor(surfaceID, surfaceCenter, surfaceNormal);

        // Parallel processor configuration
        size_t numThreads = std::thread::hardware_concurrency(); // Use max available threads
        size_t batchSize = 10000; // Number of ray paths processed in each batch

        ParallelProcessor<std::tuple<vec3d, double, double, double>> parallelProcessor(numThreads, batchSize);

        // Start timing
        auto startTime = std::chrono::high_resolution_clock::now();

        // Process ray paths and collect results
        auto results = parallelProcessor.processRayPaths(server, processor);

        // End timing
        auto endTime = std::chrono::high_resolution_clock::now();
        double elapsedTime = std::chrono::duration<double>(endTime - startTime).count();

        // Write results to a CSV file
        std::ofstream outputFile(outputfilePath);
        if (!outputFile.is_open()) {
            throw std::runtime_error("Failed to open results.csv for writing");
        }

        // Write header
        outputFile << "LocalX,LocalY,LocalZ,Length,Azimuth,Elevation\n";

        // Write results to a CSV file
        for (const auto& result : results) {
            const auto& [localCoordinates, length, azimuth, elevation] = result;
            outputFile << localCoordinates.x << "," << localCoordinates.y << "," << localCoordinates.z << ","
                       << length << "," << azimuth << "," << elevation << "\n";
        }

        outputFile.close();

        // Print elapsed time
        std::cout << "Processed all ray paths in " << elapsedTime << " seconds.\n";
    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << '\n';
        return 1;
    }

    return 0;
}