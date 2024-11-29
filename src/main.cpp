#include "raypathserver.h"
#include <iostream>
#include <chrono>
#include <vector>

int main()
{
    try {

        // Start measuring time
        auto startTime = std::chrono::high_resolution_clock::now();

        // Instantiate RaypathServer with the directory containing the Tonatiuh++ files
        RaypathServer server("C:/Users/manue_6t240gh/Dropbox/OpenSource/angular_distribution/data", "//Node/ReceiverGroup/InputAperture/InputApertureRotationX/Shape");
        server.reset(); // Reset server to start fresh for each batch size test

        const size_t batchSize = 11000000; // Maximum batch size to test

        size_t totalPhotonsRead = 0;

        // Loop until all photons are read
        while (true) {
            auto photons = server.servePhotons(batchSize);
            totalPhotonsRead += photons.size();

            // Stop if no more photons are available
            if (photons.empty()) {
                break;
            }
        }

        // Stop measuring time
        auto endTime = std::chrono::high_resolution_clock::now();
        double elapsedTime = std::chrono::duration<double>(endTime - startTime).count();

        std::cout << "Batch Size: " << batchSize
                  << ", Total Photons Read: " << totalPhotonsRead
                 << ", Time: " << elapsedTime << " seconds\n";


    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << '\n';
    }

    return 0;
}