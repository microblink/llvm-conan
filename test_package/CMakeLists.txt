project( test_package )
cmake_minimum_required( VERSION 3.18 )

set( CMAKE_CXX_STANDARD 20 )

include( ${CMAKE_BINARY_DIR}/conanbuildinfo.cmake )
conan_basic_setup()

set( CMAKE_VERBOSE_MAKEFILE TRUE )

file(GLOB SOURCE_FILES *.cpp)

add_executable(${PROJECT_NAME} ${SOURCE_FILES})
target_link_libraries(${PROJECT_NAME} ${CONAN_LIBS})

include( libcxx_windows.cmake )

add_executable(${PROJECT_NAME}_libcxx ${SOURCE_FILES})
target_link_libraries(${PROJECT_NAME}_libcxx ${CONAN_LIBS})
target_compile_definitions( ${PROJECT_NAME}_libcxx PRIVATE SHOULD_USE_LIBCXX )
