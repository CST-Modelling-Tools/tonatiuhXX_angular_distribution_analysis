#include "raypathlocalcoordinateprocessor.h"
#include <stdexcept>
#include <cmath>

RaypathLocalCoordinateProcessor::RaypathLocalCoordinateProcessor(int32_t surfaceID, const vec3d& center, const vec3d& normal)
    : m_surfaceID(surfaceID), m_center(center), m_kp(normal.normalized()) {
            // Local coordinate system
            vec3d projectionXY(m_kp.x, m_kp.y, 0.0);
            m_ip = cross(projectionXY, m_kp).normalized();
            m_jp = cross(m_kp, m_ip).normalized();
}

std::optional<RaypathLocalCoordinateProcessor::ResultType>
RaypathLocalCoordinateProcessor::processRayPath(const RayPath& rayPath) const {
    if (rayPath.photons.size() < 2) {
        return std::nullopt; // Discard ray paths with fewer than 2 photons
    }

     // Initialize photon1 and photon2
    const Photon* photon1 = &rayPath.photons[0];
    const Photon* photon2 = nullptr;   

    // Loop through the ray path
    for (size_t i = 1; i < rayPath.photons.size(); ++i) {
        photon2 = &rayPath.photons[i];

        // If photon2 is photonA
        if (photon2->surfaceID == m_surfaceID) {
            // Ensure photon1 is photonB
            if (photon1->ID != photon2->previousID) {
                throw std::runtime_error("RayPath processing error: photon1 is not photonB for photonA");
            }

            // Compute local coordinates and vectors
            vec3d photonA_coordinates(photon2->x, photon2->y, photon2->z);
            vec3d photonB_coordinates(photon1->x, photon1->y, photon1->z);

            vec3d vectorDifference = photonB_coordinates - photonA_coordinates;
            double length = vectorDifference.norm();
            vec3d directionVector = gcf::transformToLocal(vectorDifference.normalized(), m_ip, m_jp, m_kp);
            vec3d photonA_local = gcf::transformToLocal(photonA_coordinates - m_center, m_ip, m_jp, m_kp);

            double azimuth = atan2(directionVector.x, directionVector.y) / gcf::degree;
            if (azimuth < 0) azimuth += 360.0; // Normalize azimuth to [0, 360)
            double zenith_angle = acos(directionVector.z ) / gcf::degree;
            return std::make_tuple(photonA_local, length, azimuth, zenith_angle);
        }

        // If photon2 is not photonA, advance the pair
        photon1 = photon2;
    }

    return std::nullopt; // No photonA found in the ray path
}