#include "raypathdirectionsprocessor.h"
#include <stdexcept>

RaypathDirectionsProcessor::RaypathDirectionsProcessor(int32_t surfaceID) : m_surfaceID(surfaceID) {}

std::optional<RaypathDirectionsProcessor::ResultType>
RaypathDirectionsProcessor::processRayPath(const RayPath& rayPath) const {
    const Photon* photonA = nullptr;
    const Photon* photonB = nullptr;

    for (const auto& photon : rayPath.photons) {
        if (photon.surfaceID == m_surfaceID) {
            photonA = &photon;
            break;
        }
    }

    if (!photonA) {
        return std::nullopt; // Discard ray paths without a matching photon
    }

    for (const auto& photon : rayPath.photons) {
        if (photon.ID == photonA->previousID) {
            photonB = &photon;
            break;
        }
    }

    if (!photonB) {
        throw std::runtime_error("RayPath processing error: photonB not found for photonA");
    }

    vec3d photonA_coordinates(photonA->x, photonA->y, photonA->z);
    vec3d photonB_coordinates(photonB->x, photonB->y, photonB->z);

    vec3d vectorDifference = photonB_coordinates - photonA_coordinates;
    double length = vectorDifference.norm();
    vec3d directionVector = vectorDifference / length; // Normalize by dividing by length

    return std::make_tuple(photonA_coordinates, directionVector, length);
}
