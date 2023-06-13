cmake_minimum_required( VERSION 3.18 )

project( test_package )

set( CMAKE_CXX_STANDARD 20 )

set( CMAKE_VERBOSE_MAKEFILE TRUE )

file(GLOB SOURCE_FILES *.cpp)

add_subdirectory( ms_stl )
add_subdirectory( libcxx )
