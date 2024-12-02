#pragma once

#include <string>
#include <filesystem>
#include <vector>
#include <cstdint>

// Define the Photon structure
struct Photon {
    int32_t ID;           // Photon ID
    double x;             // X-coordinate
    double y;             // Y-coordinate
    double z;             // Z-coordinate
    int32_t side;         // Side information (0 or 1)
    int32_t previousID;   // Previous photon ID
    int32_t nextID;       // Next photon ID
    int32_t surfaceID;    // Surface ID
};

struct RayPath {
    std::vector<Photon> photons; // A sequence of photons forming the rayPath
};

class RaypathServer {
public:
    RaypathServer(const std::string& directoryPath, const std::string& surfacePath);
    std::vector<RayPath> serveRayPaths(size_t n);
    int32_t getReferenceSurfaceID() const { return m_surfaceID; }

private:
    std::filesystem::path m_directoryPath;
    std::filesystem::path m_metadataFile;
    std::vector<std::string> m_dataFiles;

    size_t m_currentFileIndex = 0;
    size_t m_currentPhotonIndex = 0;
    int32_t m_surfaceID = 0; // To store the surface ID associated with m_surfacePath


    static constexpr size_t recordSize = 8; // Each record contains 8 doubles

    void validateDirectory();
    void readMetadataFile();
    void validateDataFiles();
    void loadFileBuffer();
    void processPhotonsInBuffer(std::vector<RayPath>& rayPaths, size_t& rayPathsServed, size_t maxRayPaths);

    std::vector<double> m_fileBuffer; // Buffer for the current file
    std::string m_surfacePath;        // Surface path to filter
};