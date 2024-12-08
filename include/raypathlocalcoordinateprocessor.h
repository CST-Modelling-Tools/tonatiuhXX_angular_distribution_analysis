#pragma once

#include "raypathprocessor.h"
#include "vec3d.h"
#include "gcf.h"
#include <tuple>
#include <optional>

class RaypathLocalCoordinateProcessor : public RayPathProcessor<std::tuple<vec3d, double, double, double>> {
public:

    using ResultType = std::tuple<vec3d, double, double, double>; // Local coordinates, length, azimuth, elevation

    RaypathLocalCoordinateProcessor(int32_t surfaceID, const vec3d& center, const vec3d& normal);

    std::optional<ResultType> processRayPath(const RayPath& rayPath) const override;

private:
    int32_t m_surfaceID;
    vec3d m_center;
    vec3d m_ip;
    vec3d m_jp;
    vec3d m_kp;
};