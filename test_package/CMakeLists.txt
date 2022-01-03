project( test_package )
cmake_minimum_required( VERSION 3.18 )

set( CMAKE_CXX_STANDARD 20 )

include( ${CMAKE_BINARY_DIR}/conanbuildinfo.cmake )
conan_basic_setup()

set( CMAKE_VERBOSE_MAKEFILE TRUE )

file(GLOB SOURCE_FILES *.cpp)

add_subdirectory( ms_stl )
add_subdirectory( libcxx )
