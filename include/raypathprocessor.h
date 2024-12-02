#pragma once

#include <optional>
#include "raypathserver.h"

// Abstract interface for processing ray paths
template <typename ResultType>
class RayPathProcessor {
public:
    virtual ~RayPathProcessor() = default;

    // Pure virtual method for processing a ray path
    virtual std::optional<ResultType> processRayPath(const RayPath& rayPath) const = 0;
};