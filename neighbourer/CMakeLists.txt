cmake_minimum_required(VERSION 3.1)

set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 11)

project(h3examples)

find_package(h3 CONFIG REQUIRED)

# Add OpenMP support
find_package(OpenMP)
if (OPENMP_FOUND)
    set (CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    set (CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_EXE_LINKER_FLAGS}")
endif()

set(EXECUTABLE_OUTPUT_PATH bin)

set(name main)

# Build main
add_executable(${name} "${name}.cpp")
target_link_libraries(${name} PRIVATE h3::h3)

# Add compile flags
target_compile_options(${name} PRIVATE -Wall -Wextra -pedantic -O4)

# Link OpenMP
if (OPENMP_FOUND)
    target_link_libraries(${name} PRIVATE OpenMP::OpenMP_CXX)
endif()
