#pragma once

#include <string>
#include <filesystem>
#include <vector>
#include <cstdint>

struct Photon {
    int32_t ID;           // Use int32_t for photon ID
    double x;             // X-coordinate
    double y;             // Y-coordinate
    double z;             // Z-coordinate
    int32_t side;         // Side information as a double
    int32_t previousID;   // Previous photon ID
    int32_t nextID;       // Next photon ID
    int32_t surfaceID;    // Surface ID
};

class RaypathServer
{
public:
    // Constructor
    explicit RaypathServer(const std::string& directoryPath, const std::string& surfacePath);
    void reset(); // Resets internal state for fresh processing


    // Other methods will be defined later
    const std::vector<std::string>& getDataFiles() const { return m_dataFiles; }
    std::vector<Photon> servePhotons(size_t n);





private:
    std::filesystem::path m_directoryPath;
    std::filesystem::path m_metadataFile;
    std::vector<std::string> m_dataFiles;
    std::string m_surfacePath;

    int m_surfaceID;
    double m_photonPower;

    size_t m_currentFileIndex = 0;    // Tracks the current file being read
    size_t m_currentPhotonIndex = 0; // Tracks the current photon within the file

    // Helper methods
    void validateDirectory();
    void readMetadataFile();
    void validateDataFiles();
};