#pragma once

#include "raypathprocessor.h"
#include "vec3d.h"
#include <tuple>
#include <optional>

class RaypathDirectionsProcessor : public RayPathProcessor<std::tuple<vec3d, vec3d, double>> {
public:
    using ResultType = std::tuple<vec3d, vec3d, double>; // Explicitly define the ResultType for clarity
    explicit RaypathDirectionsProcessor(int32_t surfaceID);

    std::optional<ResultType> processRayPath(const RayPath& rayPath) const override;

private:
    int32_t m_surfaceID;
};
