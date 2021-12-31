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
    -isystem ${llvm_root}/include/c++/v1
)

if ( MSVC )
    MB_LLVM_add_clang_cxx_compile_options( -D_CRT_STDIO_ISO_WIDE_SPECIFIERS )
endif()

if ( MSVC )
    add_link_options( ${llvm_root}/lib/libc++.lib vcruntime.lib msvcprt.lib )
else()
    add_link_options( -L ${CMAKE_CURRENT_LIST_DIR}/lib -lc++ )
endif()
