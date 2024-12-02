#include <iostream>
#include <fstream>
#include <chrono>
#include <vector>
#include <tuple>

#include "raypathserver.h"
#include "raypathdirectionsprocessor.h"
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
        RaypathDirectionsProcessor processor(surfaceID);

        // Parallel processor configuration
        size_t numThreads = std::thread::hardware_concurrency(); // Use max available threads
        size_t batchSize = 10000; // Number of ray paths processed in each batch

        ParallelProcessor<std::tuple<vec3d, vec3d, double>> parallelProcessor(numThreads, batchSize);

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
        outputFile << "PhotonAX,PhotonAY,PhotonAZ,DirectionX,DirectionY,DirectionZ,Length\n";

        // Write each result
        for (const auto& result : results) {
            const auto& [photonA, direction, length] = result;
            outputFile << photonA.x << "," << photonA.y << "," << photonA.z << ","
                       << direction.x << "," << direction.y << "," << direction.z << ","
                       << length << "\n";
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