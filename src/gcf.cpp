#include "gcf.h"

#ifdef _WIN32
#include <windows.h>
#elif __linux__
#include <sys/sysinfo.h>
#endif

namespace gcf
{
    // Normalize angle phi to the range [phi0, phi0 + 2pi)
    double normalizeAngle(double phi, double phi0)
    {
        return phi - TwoPi * floor((phi - phi0) / TwoPi);
    }

    void SevereError(std::string errorMessage)
    {
        std::cerr << errorMessage << std::endl;
        exit(-1);
    }

    size_t getAvailableMemory()
    {
    #ifdef _WIN32
        MEMORYSTATUSEX status;
        status.dwLength = sizeof(status);
        GlobalMemoryStatusEx(&status);
        return status.ullAvailPhys;
    #elif __linux__
        struct sysinfo info;
        if (sysinfo(&info) == 0)
        {
            return info.freeram * info.mem_unit;
        }
    #endif
        return 0; // Fallback if not implemented
    }

    size_t getMemoryThreshold()
    {
        const size_t minThreshold = 256 * 1024 * 1024; // 256 MB
        const size_t maxThreshold = 2L * 1024 * 1024 * 1024; // 2 GB

        size_t availableMemory = getAvailableMemory();
        size_t threshold = availableMemory / 2; // Use 50% of available memory

        if (threshold < minThreshold)
            return minThreshold;
        if (threshold > maxThreshold)
            return maxThreshold;
        return threshold;
    }      
}