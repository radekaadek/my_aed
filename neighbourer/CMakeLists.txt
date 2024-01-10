cmake_minimum_required(VERSION 3.1)

set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 11)

project(h3examples)

find_package(h3 CONFIG REQUIRED)

set(EXECUTABLE_OUTPUT_PATH bin)

set(name main)

# Build main
add_executable(${name} "${name}.cpp")
target_link_libraries(${name} PRIVATE h3::h3)

# Add compile flags
target_compile_options(${name} PRIVATE -Wall -Wextra -pedantic)

