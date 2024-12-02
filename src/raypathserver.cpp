#include <fstream>
#include <stdexcept>
#include <iostream>
#include <sstream>

#include "raypathserver.h"
#include "gcf.h"

namespace fs = std::filesystem;

// Constructor
RaypathServer::RaypathServer(const std::string& directoryPath, const std::string& surfacePath)
    : m_directoryPath(directoryPath),  m_surfacePath(surfacePath) {
    validateDirectory();
    readMetadataFile();
    validateDataFiles();
}

// Validate the directory and locate the metadata file
void RaypathServer::validateDirectory() {
    if (!fs::exists(m_directoryPath) || !fs::is_directory(m_directoryPath)) {
        throw std::invalid_argument("Invalid directory path: " + m_directoryPath.string());
    }

    bool metadataFound = false;
    for (const auto& entry : fs::directory_iterator(m_directoryPath)) {
        if (entry.is_regular_file() && entry.path().extension() == ".txt") {
            m_metadataFile = entry.path();
            metadataFound = true;
            break;
        }
    }

    if (!metadataFound) {
        throw std::runtime_error("No metadata .txt file found in directory: " + m_directoryPath.string());
    }
}

void RaypathServer::readMetadataFile() {
    std::ifstream file(m_metadataFile);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open metadata file: " + m_metadataFile.string());
    }

    std::string line;
    bool parametersSectionStarted = false;
    bool parametersSectionEnded = false;
    bool surfacesSectionStarted = false;

    static const std::vector<std::string> expectedParameters = {
        "id", "x", "y", "z", "side", "previous ID", "next ID", "surface ID"
    };

    while (std::getline(file, line)) {
        // Clean up the line by trimming trailing whitespace
        line.erase(line.find_last_not_of(" \t\r\n") + 1);

        if (line == "START PARAMETERS") {
            if (parametersSectionStarted) {
                throw std::runtime_error("Duplicate START PARAMETERS found in metadata file.");
            }
            parametersSectionStarted = true;
        } else if (line == "END PARAMETERS") {
            if (!parametersSectionStarted) {
                throw std::runtime_error("END PARAMETERS found before START PARAMETERS in metadata file.");
            }
            parametersSectionEnded = true;
        } else if (parametersSectionStarted && !parametersSectionEnded) {
            // Validate parameters
            if (std::find(expectedParameters.begin(), expectedParameters.end(), line) == expectedParameters.end()) {
                throw std::runtime_error("Unexpected parameter in PARAMETERS section: " + line);
            }
        } else if (line == "START SURFACES") {
            surfacesSectionStarted = true;
        } else if (surfacesSectionStarted && line.find(m_surfacePath) != std::string::npos) {
            // Extract the first number as surface ID
            std::istringstream iss(line);
            iss >> m_surfaceID;

            if (iss.fail()) {
                throw std::runtime_error("Failed to parse surfaceID for surface path: " + m_surfacePath);
            }
        }
    }

    // Ensure PARAMETERS section was properly delimited
    if (!parametersSectionStarted || !parametersSectionEnded) {
        throw std::runtime_error("PARAMETERS section is incomplete in metadata file.");
    }

    // Ensure the SURFACES section was reached
    if (!surfacesSectionStarted) {
        throw std::runtime_error("SURFACES section not found in metadata file.");
    }
}

// Validate .dat files
void RaypathServer::validateDataFiles() {
    for (const auto& entry : fs::directory_iterator(m_directoryPath)) {
        if (entry.is_regular_file() && entry.path().extension() == ".dat") {
            m_dataFiles.push_back(entry.path().string());
        }
    }

    if (m_dataFiles.empty()) {
        throw std::runtime_error("No .dat files found in directory: " + m_directoryPath.string());
    }

    // Sort files by their names (if numeric sorting is required, adjust logic)
    std::sort(m_dataFiles.begin(), m_dataFiles.end());
}

// Serve ray paths
std::vector<RayPath> RaypathServer::serveRayPaths(size_t n) {
    std::vector<RayPath> rayPaths;
    size_t rayPathsServed = 0;

    while (rayPathsServed < n) {
        if (m_fileBuffer.empty() || m_currentPhotonIndex >= m_fileBuffer.size() / recordSize) {
            if (m_currentFileIndex >= m_dataFiles.size()) {
                break; // No more files to read
            }
            loadFileBuffer();
        }

        processPhotonsInBuffer(rayPaths, rayPathsServed, n);
    }

    return rayPaths;
}

void RaypathServer::loadFileBuffer() {
    // Open the current .dat file
    const auto& dataFile = m_dataFiles[m_currentFileIndex];
    std::ifstream file(dataFile, std::ios::binary);

    if (!file.is_open()) {
        throw std::runtime_error("Failed to open .dat file: " + dataFile);
    }

    // Determine the file size
    file.seekg(0, std::ios::end);
    size_t fileSize = file.tellg();
    file.seekg(0, std::ios::beg);

    // Calculate the number of records in the file
    size_t numRecords = fileSize / (recordSize * sizeof(double));

    // Resize the buffer to hold all the photons in the file
    m_fileBuffer.resize(numRecords * recordSize);

    // Read the file into the buffer
    file.read(reinterpret_cast<char*>(m_fileBuffer.data()), fileSize);

    if (file.gcount() != static_cast<std::streamsize>(fileSize)) {
        throw std::runtime_error("Error reading data from .dat file: " + dataFile);
    }

    // Convert data to native endianness if necessary
    for (size_t i = 0; i < m_fileBuffer.size(); ++i) {
        m_fileBuffer[i] = gcf::convertToNativeEndian(m_fileBuffer[i]);
    }

    // Reset the photon index for the newly loaded file
    m_currentPhotonIndex = 0;

    // Move to the next file for subsequent reads
    m_currentFileIndex++;
}

void RaypathServer::processPhotonsInBuffer(std::vector<RayPath>& rayPaths, size_t& rayPathsServed, size_t maxRayPaths) {
    RayPath currentRayPath; // Declare the currentRayPath variable

    while (m_currentPhotonIndex < m_fileBuffer.size() / recordSize) {
        Photon photon;

        size_t offset = m_currentPhotonIndex * recordSize;
        photon.ID = static_cast<int32_t>(m_fileBuffer[offset + 0]);
        photon.x = m_fileBuffer[offset + 1];
        photon.y = m_fileBuffer[offset + 2];
        photon.z = m_fileBuffer[offset + 3];
        photon.side = static_cast<int32_t>(m_fileBuffer[offset + 4]);
        photon.previousID = static_cast<int32_t>(m_fileBuffer[offset + 5]);
        photon.nextID = static_cast<int32_t>(m_fileBuffer[offset + 6]);
        photon.surfaceID = static_cast<int32_t>(m_fileBuffer[offset + 7]);

        m_currentPhotonIndex++;

        if (photon.previousID == 0) {
            // This indicates the start of a new ray path
            if (!currentRayPath.photons.empty()) {
                // Only add ray paths with two or more photons
                if (currentRayPath.photons.size() > 1) {
                    rayPaths.push_back(currentRayPath);
                    rayPathsServed++;
                }
                currentRayPath.photons.clear();

                if (rayPathsServed >= maxRayPaths) {
                    return;
                }
            }
        }

        currentRayPath.photons.push_back(photon);

        if (photon.nextID == 0) {
            // This indicates the end of the current ray path
            if (currentRayPath.photons.size() > 1) {
                rayPaths.push_back(currentRayPath);
                rayPathsServed++;
            }
            currentRayPath.photons.clear();

            if (rayPathsServed >= maxRayPaths) {
                return;
            }
        }
    }
}