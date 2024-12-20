#pragma once

#include "vec2d.h"
#include <string>

struct vec3d
{
    vec3d(double x = 0., double y = 0., double z = 0.):
        x(x), y(y), z(z) {}

    vec3d(const vec2d& v, double z = 0.):
        x(v.x), y(v.y), z(z) {}

    vec3d(float* p):
        x(*p), y(*(p + 1)), z(*(p + 2)) {}

    vec3d(double* p):
        x(*p), y(*(p + 1)), z(*(p + 2)) {}

    // constants
    static const vec3d Zero;
    static const vec3d One;
    static const vec3d UnitX;
    static const vec3d UnitY;
    static const vec3d UnitZ;

    vec3d operator+(const vec3d& v) const
    {
        return vec3d(x + v.x, y + v.y, z + v.z);
    }

    vec3d& operator+=(const vec3d& v)
    {
        x += v.x;
        y += v.y;
        z += v.z;
        return *this;
    }

    vec3d operator-() const
    {
        return vec3d(-x, -y, -z);
    }

    vec3d operator-(const vec3d& v) const
    {
        return vec3d(x - v.x, y - v.y, z - v.z);
    }

    vec3d& operator-=(const vec3d& v)
    {
        x -= v.x;
        y -= v.y;
        z -= v.z;
        return *this;
    }

    vec3d operator*(double s) const
    {
        return vec3d(x*s, y*s, z*s);
    }

    vec3d operator*(const vec3d& v) const
    {
        return vec3d(x*v.x, y*v.y, z*v.z);
    }

    vec3d& operator*=(double s)
    {
        x *= s;
        y *= s;
        z *= s;
        return *this;
    }

    vec3d operator/(double s) const
    {
        s = 1./s;
        return vec3d(x*s, y*s, z*s);
    }

    vec3d operator/(const vec3d& v) const
    {
        return vec3d(x/v.x, y/v.y, z/v.z);
    }

    vec3d& operator/=(double s)
    {
        s = 1./s;
        x *= s;
        y *= s;
        z *= s;
        return *this;
    }

    bool operator==(const vec3d& v) const;
    bool operator!=(const vec3d& v) const;
    bool operator<=(const vec3d& v) const {return x <= v.x && y <= v.y && z < v.z;}

    double operator[](int i) const
    {
        if (i == 0) return x;
        if (i == 1) return y;
        return z;
    }

    double& operator[](int i)
    {
        if (i == 0) return x;
        if (i == 1) return y;
        return z;
    }

    double norm2() const {
        return x*x + y*y + z*z;
    }

    double norm() const {
        return std::sqrt(norm2());
    }

    vec3d normalized() const
    {
        double s = norm2();
        if (s > 0.)
            return *this/sqrt(s);
        return *this;
    }

    bool normalize()
    {
        double s = norm2();
        if (s > 0.) {
            *this /= sqrt(s);
            return true;
        }
        return false;
    }

    vec3d projected(const vec3d& n) const;
    vec3d reflected(const vec3d& n) const;
    vec3d reflect(const vec3d& v) const;

    double min() const {return std::min(std::min(x, y), z);}
    double max() const {return std::max(std::max(x, y), z);}
    vec3d abs() const {return vec3d(std::abs(x), std::abs(y), std::abs(z));}
    int maxDimension() const;

    vec3d findOrthogonal() const;

    double x;
    double y;
    double z;

    static vec3d min(const vec3d& a, const vec3d& b)
    {
        return vec3d(
            std::min(a.x, b.x),
            std::min(a.y, b.y),
            std::min(a.z, b.z)
        );
    }

    static vec3d max(const vec3d& a, const vec3d& b)
    {
        return vec3d(
            std::max(a.x, b.x),
            std::max(a.y, b.y),
            std::max(a.z, b.z)
        );
    }

    static vec3d directionAE(double azimuth, double elevation);
};

inline vec3d operator*(double s, const vec3d& v)
{
    return vec3d(s*v.x, s*v.y, s*v.z);
}

inline double dot(const vec3d& a, const vec3d& b)
{
    return a.x*b.x + a.y*b.y + a.z*b.z;
}

inline vec3d cross(const vec3d& a, const vec3d& b)
{
    return vec3d(
        a.y*b.z - a.z*b.y,
        a.z*b.x - a.x*b.z,
        a.x*b.y - a.y*b.x
    );
}

inline double triple(const vec3d& a, const vec3d& b, const vec3d& c)
{
    return dot(a, cross(b, c));
}

// this != normal
inline vec3d vec3d::projected(const vec3d& n) const
{
    // This computes the orthogonal projection of "*this" onto a plane 
    // defined by its normal vector n.
    // It is assumed that n is a unit vector.
    return *this - n*dot(*this, n);
}

// this != normal
inline vec3d vec3d::reflected(const vec3d& n) const
{
    // This computes the the reflection of "*this" onto a plane 
    // defined by its normal vector n.
    // It is assumed that n is a unit vector.
    return *this - n*(2.*dot(*this, n));
}

// this = normal
inline vec3d vec3d::reflect(const vec3d& v) const
{
    return v - (*this)*(2.*dot(*this, v)/norm2());
}

inline vec3d vec3d::findOrthogonal() const
{
    if (std::abs(z) > std::abs(x) && std::abs(z) > std::abs(y))
        return vec3d(z, 0., -x);
    else
        return vec3d(y, -x, 0.);
}

std::ostream& operator<<(std::ostream& os, const vec3d& vector);