#include "vec2d.h"
#include "gcf.h"

const vec2d vec2d::Zero(0., 0.);
const vec2d vec2d::One(1., 1.);
const vec2d vec2d::UnitX(1., 0.);
const vec2d vec2d::UnitY(0., 1.);

bool vec2d::operator==(const vec2d& v) const
{
    if (this == &v) return true;

    return gcf::equals(x, v.x) && gcf::equals(y, v.y);
}

bool vec2d::operator!=(const vec2d& v) const
{
    return !(*this == v);
}

std::ostream& operator<<(std::ostream& os, const vec2d& v)
{
    os << v.x << ", " << v.y;
    return os;
}