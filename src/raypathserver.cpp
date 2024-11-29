#include <iostream>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <algorithm>

#include "gcf.h"
#include "raypathserver.h"

namespace fs = std::filesystem;

RaypathServer::RaypathServer(const std::string& directoryPath, const std::string& surfacePath)
    : m_directoryPath(directoryPath), m_surfacePath(surfacePath), m_surfaceID(-1), m_photonPower(0.0)
{
    validateDirectory();
    readMetadataFile();
    validateDataFiles();
}

void RaypathServer::reset()
{
    m_currentFileIndex = 0;   // Reset file index
    m_currentPhotonIndex = 0; // Reset photon index within the file
}

void RaypathServer::validateDirectory()
{
    // Check if the directory exists
    if (!fs::exists(m_directoryPath) || !fs::is_directory(m_directoryPath)) {
        throw std::invalid_argument("Invalid directory path: " + m_directoryPath.string());
    }

    // Look for the .txt file containing metadata
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

void RaypathServer::readMetadataFile()
{
    // Open the metadata file
    std::ifstream file(m_metadataFile);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open metadata file: " + m_metadataFile.string());
    }

    // Variables to track state
    bool parametersSectionStarted = false;
    bool parametersSectionEnded = false;
    bool surfacesSectionStarted = false;
    std::string line;

    while (std::getline(file, line)) {
        // Strip whitespace
        line.erase(line.find_last_not_of(" \t\r\n") + 1);

        // Check the PARAMETERS section structure
        if (line == "START PARAMETERS") {
            parametersSectionStarted = true;
            continue;
        }
        if (line == "END PARAMETERS") {
            if (!parametersSectionStarted) {
                throw std::runtime_error("END PARAMETERS found without START PARAMETERS.");
            }
            parametersSectionEnded = true;
            continue;
        }
        if (parametersSectionStarted && !parametersSectionEnded) {
            static const std::vector<std::string> expectedParameters = {
                "id", "x", "y", "z", "side", "previous ID", "next ID", "surface ID"};
            if (std::find(expectedParameters.begin(), expectedParameters.end(), line) == expectedParameters.end()) {
                throw std::runtime_error("Unexpected parameter in PARAMETERS section: " + line);
            }
        }

        // Look for the surfacePath in the SURFACES section
        if (line == "START SURFACES") {
            surfacesSectionStarted = true;
            continue;
        }
        if (surfacesSectionStarted && line.find(m_surfacePath) != std::string::npos) {
            std::istringstream iss(line);
            iss >> m_surfaceID; // Extract the first number as surface ID
            if (iss.fail()) {
                throw std::runtime_error("Failed to parse surface ID for surface path: " + m_surfacePath);
            }
        }
    }

    // Ensure the PARAMETERS section structure is complete
    if (!parametersSectionStarted || !parametersSectionEnded) {
        throw std::runtime_error("Incomplete PARAMETERS section in metadata file.");
    }

    // Get the power associated with each photon from the last line of text
    std::string lastTextLine;
    file.clear();
    file.seekg(0, std::ios::beg);
    while (std::getline(file, line)) {
        if (!line.empty()) {
            lastTextLine = line;
        }
    }
    std::istringstream iss(lastTextLine);
    if (!(iss >> m_photonPower)) {
        throw std::runtime_error("Failed to parse photon power from the last line of the metadata file.");
    }

    file.close();

    std::cout << "Metadata successfully read.\n";
    std::cout << "Surface ID: " << m_surfaceID << "\n";
    std::cout << "Photon Power: " << m_photonPower << " W\n";
}

void RaypathServer::validateDataFiles()
{
    std::vector<std::pair<int, std::string>> fileIndexPairs;

    // Look for .dat files in the directory
    for (const auto& entry : fs::directory_iterator(m_directoryPath)) {
        if (entry.is_regular_file() && entry.path().extension() == ".dat") {
            std::string filename = entry.path().filename().string();
            size_t underscorePos = filename.find('_');
            size_t dotPos = filename.rfind('.');

            if (underscorePos != std::string::npos && dotPos != std::string::npos) {
                try {
                    int fileIndex = std::stoi(filename.substr(underscorePos + 1, dotPos - underscorePos - 1));
                    fileIndexPairs.emplace_back(fileIndex, entry.path().string());
                } catch (const std::invalid_argument&) {
                    throw std::runtime_error("Failed to parse number from file: " + filename);
                }
            }
        }
    }

    if (fileIndexPairs.empty()) {
        throw std::runtime_error("No .dat files found in directory: " + m_directoryPath.string());
    }

    // Sort files by the extracted number
    std::sort(fileIndexPairs.begin(), fileIndexPairs.end(), [](const auto& a, const auto& b) {
        return a.first < b.first;
    });

    // Store sorted file paths
    for (const auto& pair : fileIndexPairs) {
        m_dataFiles.emplace_back(pair.second);
    }

    std::cout << "Found and sorted " << m_dataFiles.size() << " .dat files.\n";
}

std::vector<Photon> RaypathServer::servePhotons(size_t n)
{
    std::vector<Photon> photons;
    size_t photonsServed = 0;

    const size_t memoryThreshold = gcf::getMemoryThreshold();
    const size_t maxDoublesPerBatch = memoryThreshold / sizeof(double);
    const size_t maxPhotonsPerBatch = maxDoublesPerBatch / 8; // 8 doubles per photon record

    while (photonsServed < n && m_currentFileIndex < m_dataFiles.size())
    {
        const auto &dataFile = m_dataFiles[m_currentFileIndex];
        std::ifstream file(dataFile, std::ios::binary);

        if (!file.is_open())
        {
            throw std::runtime_error("Failed to open .dat file: " + dataFile);
        }

        // Move file pointer to the current photon position
        file.seekg(m_currentPhotonIndex * 8 * sizeof(double), std::ios::beg);

        // Calculate remaining records in the current file
        file.seekg(0, std::ios::end);
        size_t totalRecordsInFile = file.tellg() / (8 * sizeof(double));
        file.seekg(m_currentPhotonIndex * 8 * sizeof(double), std::ios::beg);

        size_t remainingRecordsInFile = totalRecordsInFile - m_currentPhotonIndex;
        size_t recordsToRead = std::min({n - photonsServed, remainingRecordsInFile, maxPhotonsPerBatch});

        // Read batch of doubles
        std::vector<double> buffer(recordsToRead * 8); // 8 doubles per photon
        file.read(reinterpret_cast<char *>(buffer.data()), recordsToRead * 8 * sizeof(double));

        if (file.gcount() != recordsToRead * 8 * sizeof(double))
        {
            throw std::runtime_error("Error reading photon data from file: " + dataFile);
        }

        // Convert data to native endianness and populate the Photon structures
        for (size_t i = 0; i < recordsToRead; ++i)
        {
            Photon photon;
            photon.ID = static_cast<int32_t>( gcf::convertToNativeEndian(buffer[i * 8 + 0]) );
            photon.x = gcf::convertToNativeEndian(buffer[i * 8 + 1]);
            photon.y = gcf::convertToNativeEndian(buffer[i * 8 + 2]);
            photon.z = gcf::convertToNativeEndian(buffer[i * 8 + 3]);
            photon.side = static_cast<int32_t>( gcf::convertToNativeEndian(buffer[i * 8 + 4]) );
            photon.previousID = static_cast<int32_t>( gcf::convertToNativeEndian(buffer[i * 8 + 5]) );
            photon.nextID = static_cast<int32_t>( gcf::convertToNativeEndian(buffer[i * 8 + 6]) );
            photon.surfaceID = static_cast<int32_t>( gcf::convertToNativeEndian(buffer[i * 8 + 7]) );

            photons.push_back(photon);
            photonsServed++;
        }

        m_currentPhotonIndex += recordsToRead;
        if (m_currentPhotonIndex >= totalRecordsInFile)
        {
            m_currentPhotonIndex = 0;
            m_currentFileIndex++;
        }
    }

    // if (photonsServed < n)
    // {
    //     std::cerr << "Warning: Requested " << n << " photons, but only " << photonsServed << " available.\n";
    // }

    return photons;
}