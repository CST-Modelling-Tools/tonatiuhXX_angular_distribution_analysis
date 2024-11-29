#pragma once

#include <bit>
#include <cfloat>
#include <cmath>
#include <cstdint>
#include <string>
#include <stdexcept>
#include <cstring>
#include <fstream>
#include <vector>
#include <filesystem>
#include <iostream>

// global constants and functions
namespace gcf
{
    const double Pi = 3.1415926535897932385;
    const double TwoPi = 2.*Pi;
    const double degree = Pi/180.0;
    const double infinity = HUGE_VAL;
    const double Epsilon = DBL_EPSILON;

    // Enum for endianness
    enum class Endianness { Big, Little, Mixed };

    // Determine the system's endianness at compile time
    static const Endianness SystemEndianness = 
        (std::endian::native == std::endian::big)   ? Endianness::Big :
        (std::endian::native == std::endian::little)? Endianness::Little :
                                                      Endianness::Mixed;        

    template<class T>
    bool equals(T x, T y)
    {
        return std::abs(x - y) < std::numeric_limits<T>::epsilon();
    }

    double normalizeAngle(double phi, double phi0);
    void SevereError(std::string errorMessage);

   // Function to handle endianness conversion
    inline double convertToNativeEndian(double value)
    {
        if (SystemEndianness == Endianness::Little) {
            uint64_t temp = std::byteswap(*reinterpret_cast<uint64_t*>(&value));
            return *reinterpret_cast<double*>(&temp);
        } else if (SystemEndianness == Endianness::Big) {
            return value; // No conversion needed for big-endian systems
        } else {
            throw std::runtime_error("Unsupported or mixed-endian system.");
        }
    }

    // Get system memory information
    size_t getAvailableMemory();
    size_t getMemoryThreshold();    
}