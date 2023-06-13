
include( libcxx_windows.cmake )

add_executable(${PROJECT_NAME}_libcxx ${SOURCE_FILES})
target_compile_definitions( ${PROJECT_NAME}_libcxx PRIVATE SHOULD_USE_LIBCXX )
