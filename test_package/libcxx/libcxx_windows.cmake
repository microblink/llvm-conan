include_guard()

# include this CMake module to setup your project to use libc++ instead of MS STL
get_filename_component( llvm_bin "${CMAKE_CXX_COMPILER}" DIRECTORY )
get_filename_component( llvm_root "${llvm_bin}" DIRECTORY )

function( MB_LLVM_add_cxx_compile_options )
    if( ${CMAKE_GENERATOR} MATCHES "Visual Studio" )
        add_compile_options( ${ARGV} )
    else()
        foreach( arg ${ARGV} )
            add_compile_options( $<$<COMPILE_LANGUAGE:CXX>:${arg}> )
        endforeach()
    endif()
endfunction()

function( MB_LLVM_add_clang_cxx_compile_options )
    if ( MSVC AND CMAKE_CXX_COMPILER_ID STREQUAL "Clang" )
        if( ${CMAKE_GENERATOR} MATCHES "Visual Studio" )
            foreach( arg ${ARGV} )
                add_compile_options( /clang:${arg} )
            endforeach()
        else()
            foreach( arg ${ARGV} )
                add_compile_options( $<$<COMPILE_LANGUAGE:CXX>:/clang:${arg}> )
            endforeach()
        endif()
    else()
        MB_LLVM_add_cxx_compile_options( ${ARGV} )
    endif()
endfunction()

MB_LLVM_add_clang_cxx_compile_options(
    -nostdinc++
    -nostdlib
)

if( ${CMAKE_GENERATOR} MATCHES "Visual Studio" )
    include_directories( BEFORE SYSTEM ${llvm_root}/include/c++/v1 )
else()
    include_directories( BEFORE SYSTEM $<$<COMPILE_LANGUAGE:CXX>:${llvm_root}/include/c++/v1> )
endif()

if ( CMAKE_SYSTEM_PROCESSOR STREQUAL ARM64 )
    set( arch "aarch64" )
else()
    set( arch "x86_64" )
endif()

if( ${CMAKE_GENERATOR} MATCHES "Visual Studio" )
    set( libcxx_includes ${llvm_root}/include/c++/v1 ${llvm_root}/include/${arch}-pc-windows-msvc/c++/v1 )
else()
    set( libcxx_includes $<$<COMPILE_LANGUAGE:CXX>:${llvm_root}/include/c++/v1>  $<$<COMPILE_LANGUAGE:CXX>:${llvm_root}/include/${arch}-pc-windows-msvc/c++/v1> )
endif()
include_directories( BEFORE ${libcxx_includes} )

if ( MSVC )
    MB_LLVM_add_clang_cxx_compile_options( -D_CRT_STDIO_ISO_WIDE_SPECIFIERS )
endif()

if ( MSVC )
    if ( CMAKE_HOST_SYSTEM_PROCESSOR STREQUAL ARM64 )
        set( suffix "aarch64" )
    else()
        set( suffix "x86_64" )
    endif()
    string( REPLACE "." ";" VERSION_LIST ${CMAKE_CXX_COMPILER_VERSION} )
    list( GET VERSION_LIST 0 compiler_major_version  )
    add_link_options(
        "${llvm_root}/lib/${arch}-pc-windows-msvc/libc++.lib"
        "${MB_LLVM_ROOT}/lib/clang/${compiler_major_version}/lib/${arch}-pc-windows-msvc/clang_rt.builtins.lib"
        vcruntime.lib
        msvcprt.lib
    )
else()
    add_link_options( -L ${CMAKE_CURRENT_LIST_DIR}/lib -L ${CMAKE_CURRENT_LIST_DIR}/lib/${arch}-pc-windows-msvc -lc++ )
endif()
