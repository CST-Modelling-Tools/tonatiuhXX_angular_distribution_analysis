# Minimum version of CMake
cmake_minimum_required(VERSION 3.14)

# Project name
project(RayTracing)

# C++ Standard
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Include directory
include_directories(include)

# Source files
set(SOURCES
    src/main.cpp
    src/gcf.cpp
    src/vec2d.cpp
    src/vec3d.cpp
    src/raypathserver.cpp
    # Add more source files here if needed later
)

# Add executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Target include directories for the executable
target_include_directories(${PROJECT_NAME} PRIVATE include)

# Platform-specific configurations
if (CMAKE_SYSTEM_NAME STREQUAL "Windows")
    message(STATUS "Compiling on Windows")
    target_compile_definitions(${PROJECT_NAME} PRIVATE _USE_MATH_DEFINES)
elseif (CMAKE_SYSTEM_NAME STREQUAL "Darwin")  # macOS
    message(STATUS "Compiling on macOS")
    target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra)
elseif (CMAKE_SYSTEM_NAME STREQUAL "Linux")
    message(STATUS "Compiling on Linux")
    target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra -pedantic)
endif()
