cmake_minimum_required(VERSION 3.10)
project(compute_directions)

# Find Python and pybind11
find_package(Python COMPONENTS Interpreter Development REQUIRED)
if (Python_FOUND)
    message(STATUS "Found Python interpreter at: ${Python_EXECUTABLE}")   

    execute_process(
        COMMAND ${Python_EXECUTABLE} -c "import pybind11; print(pybind11.get_include())"
        OUTPUT_VARIABLE PYBIND11_INCLUDE_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    if (PYBIND11_INCLUDE_DIR AND EXISTS "${PYBIND11_INCLUDE_DIR}/pybind11/embed.h")
        message(STATUS "Found pybind11 include directory: ${PYBIND11_INCLUDE_DIR}")
        include_directories(${PYBIND11_INCLUDE_DIR})
        execute_process(
            COMMAND ${Python_EXECUTABLE} -m pybind11 --cmake
            OUTPUT_VARIABLE pybind11_DIR
            ERROR_VARIABLE error
            RESULT_VARIABLE result
            OUTPUT_STRIP_TRAILING_WHITESPACE
            ERROR_STRIP_TRAILING_WHITESPACE
        )
        if (result EQUAL 0 AND EXISTS "${pybind11_DIR}/pybind11Config.cmake")
            message(STATUS "Found pybind11 at: ${pybind11_DIR}")
            list(APPEND CMAKE_PREFIX_PATH ${pybind11_DIR})
            find_package(pybind11 CONFIG REQUIRED)
        else()
            message(WARNING "pybind11 not found. Error: ${error}")
        endif()
    else()
        message(WARNING "pybind11 include directory not found.")
    endif()
else()
    message(STATUS "Python not found. Not generating Python wrappers.")
endif()

# Add the source file
add_library(compute_directions MODULE compute_directions.cpp)

# Link the Python and pybind11 libraries
if (TARGET pybind11::module)
    target_link_libraries(compute_directions PRIVATE pybind11::module Python::Python)
endif()

# Set the output properties for shared library compatibility
set_target_properties(compute_directions PROPERTIES PREFIX "")

# Ensure correct extension for Python modules on Windows
if (WIN32)
    set_target_properties(compute_directions PROPERTIES SUFFIX ".pyd")
else()
    set_target_properties(compute_directions PROPERTIES SUFFIX ".so")
endif()

# Enable C++17 standard
target_compile_features(compute_directions PRIVATE cxx_std_17)

# Platform-specific compiler options
if (WIN32)
    target_compile_definitions(compute_directions PRIVATE -D_USE_MATH_DEFINES)
elseif(APPLE)
    target_compile_options(compute_directions PRIVATE -std=c++17)
elseif(UNIX)
    target_compile_options(compute_directions PRIVATE -std=c++17)
endif()