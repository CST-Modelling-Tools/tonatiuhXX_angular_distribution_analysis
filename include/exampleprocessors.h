#pragma once

#include <iostream>
#include <cmath>

#include "raypathprocessor.h"

// A processor that calculates the length of each ray path
class RayLengthProcessor : public RayPathProcessor {
public:
    void processRayPath(const RayPath& rayPath) const override {
        double totalLength = 0.0;
        for (size_t i = 1; i < rayPath.photons.size(); ++i) {
            const auto& p1 = rayPath.photons[i - 1];
            const auto& p2 = rayPath.photons[i];
            totalLength += std::sqrt(std::pow(p2.x - p1.x, 2) +
                                     std::pow(p2.y - p1.y, 2) +
                                     std::pow(p2.z - p1.z, 2));
        }
//        std::cout << "Ray path length: " << totalLength << '\n';
    }
};

// A processor that counts photons in each ray path
class PhotonCountProcessor : public RayPathProcessor {
public:
    void processRayPath(const RayPath& rayPath) const override {
        std::cout << "Ray path has " << rayPath.photons.size() << " photons.\n";
    }
};

