cmake_minimum_required( VERSION 3.18 )

project( test_package )

set( CMAKE_CXX_STANDARD 20 )

set( CMAKE_VERBOSE_MAKEFILE TRUE )

set( SOURCE_FILES test.cpp )

add_executable( ${PROJECT_NAME} ${SOURCE_FILES} )
