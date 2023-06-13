from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.microsoft import VCVars
from conan.tools.cmake import CMakeToolchain, cmake_layout, CMake
from conan.tools.files import copy
from conan.tools.scm import Git, Version
import os

# Package build instructions:
# - initialize your terminal with vcvars
# - set cc and cxx to clang-cl of the previous version of clang, that will be used for building the new package
# - run following command:
# conan create . microblink/stable -pr clang-windows-generic-x64 -s compiler.version=<version-used-for-building> -tf=None


class LLVMConan(ConanFile):
    name = "llvm"
    version = "16.0.5"
    url = "https://github.com/microblink/llvm-conan"
    license = "Apache 2.0 WITH LLVM-exception"
    description = "LLVM toolchain with custom build of libc++"
    topics = ('llvm', 'compiler')
    settings = "os", "arch", "build_type", "compiler"
    no_copy_source = True
    options = {
        'use_clang_cl': [True, False]
    }

    def config_options(self):
        self.options.use_clang_cl = self.settings.os == 'Windows'

    def source(self):
        git = Git(self)
        git.clone(
            'https://github.com/microblink/llvm-project',
            target=self.source_folder,
            args=['--depth 1', f'--branch microblink-llvmorg-{self.version}']
        )

    def validate(self):
        if self.settings.os != 'Windows':
            raise ConanInvalidConfiguration('At the moment, this package supports only Windows')

    def layout(self):
        cmake_layout(self, generator='Ninja', src_folder='llvm-src')

    def generate(self):
        vcars = VCVars(self)
        vcars.generate()

        additional_cc_flags = '/clang:-Ofast'
        if self.settings.arch == 'x86_64':
            additional_cc_flags += ' /clang:-mavx /clang:-mavx2 /clang:-mfma'

        cmake = CMakeToolchain(self)
        cmake.cache_variables.update(
            {
                'CMAKE_BUILD_TYPE': 'Release',
                # 'LLVM_ENABLE_PROJECTS': 'clang;lld;lldb;compiler-rt;polly',
                'LLVM_ENABLE_PROJECTS': 'clang;lld;lldb;compiler-rt',
                'LLVM_ENABLE_RUNTIMES': '"libcxx"',
                'LLVM_TARGETS_TO_BUILD': 'AArch64;ARM;WebAssembly;X86',
                # 'LLVM_ENABLE_LTO': 'Thin',
                'LLVM_PARALLEL_LINK_JOBS': '3',
                'LLVM_USE_LINKER': '"lld"',
                'LLVM_ENABLE_EH': 'OFF',
                'LLVM_ENABLE_RTTI': 'OFF',
                # 'LLVM_BUILD_LLVM_DYLIB': 'ON',
                # 'LLVM_LINK_LLVM_DYLIB': 'ON',
                'LLVM_ENABLE_PER_TARGET_RUNTIME_DIR': 'ON',
                'LLVM_INCLUDE_TESTS': 'OFF',
                'LLVM_INCLUDE_BENCHMARKS': 'OFF',
                'CLANG_DEFAULT_LINKER': 'lld',
                'CLANG_DEFAULT_RTLIB': 'compiler-rt',
                'LIBCXX_USE_COMPILER_RT': 'YES',
                'LIBCXX_ABI_VERSION': '2',
                'LIBCXX_ABI_UNSTABLE': 'ON',
                'LIBCXX_ENABLE_EXCEPTIONS': 'OFF',
                'LIBCXX_ENABLE_RTTI': 'ON',
                'LIBCXX_ENABLE_SHARED': 'OFF',
                'LIBCXX_ENABLE_FILESYSTEM': 'ON',
                'LIBCXX_INCLUDE_BENCHMARKS': 'OFF',
                'LIBCXX_INCLUDE_TESTS': 'OFF',
                'LIBCXX_INCLUDE_DOCS': 'OFF',
                'CMAKE_C_FLAGS': f'-fsplit-lto-unit {additional_cc_flags}',
                'CMAKE_CXX_FLAGS': f'-fsplit-lto-unit {additional_cc_flags}',
            }
        )
        cmake.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, 'llvm'))
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(
            self,
            pattern='libcxx_windows.cmake',
            src=self.source_folder,
            dst=os.path.join(self.package_folder, 'cmake', 'Modules')
        )

    def package_id(self):
        del self.info.options.use_clang_cl
        del self.info.settings.compiler
        del self.info.settings.build_type

    def package_info(self):
        self.cpp_info.builddirs = [
            os.path.join('cmake', 'Modules')
        ]

        compiler_executables = {
            "c": self._define_tool_var('clang-cl' if self.options.use_clang_cl else 'clang'),
            "cpp": self._define_tool_var('clang-cl' if self.options.use_clang_cl else 'clang++')  # noqa: E501
        }

        self.conf_info.update('tools.build:compiler_executables', compiler_executables)
        self.buildenv_info.define_path("CC", compiler_executables["c"])
        self.buildenv_info.define_path("CXX", compiler_executables["cpp"])

        self.buildenv_info.define_path("LD", self._define_tool_var(
            'lld-link' if self.settings.os == 'Windows' else 'lld'))
        self.buildenv_info.define_path("AR", self._define_tool_var('llvm-ar'))
        self.buildenv_info.define_path("RANLIB", self._define_tool_var('llvm-ranlib'))
        self.buildenv_info.define_path("STRIP", self._define_tool_var('llvm-strip'))
        self.buildenv_info.define_path("NM", self._define_tool_var('llvm-nm'))
        self.buildenv_info.define_path("OBJCOPY", self._define_tool_var('llvm-objcopy'))
        self.buildenv_info.define_path("OBJDUMP", self._define_tool_var('llvm-bjdump'))
        self.buildenv_info.define_path("READELF", self._define_tool_var('llvm-readobj'))

        if self.settings.compiler.libcxx == 'libc++v2':
            if self.settings.arch == 'armv8':
                arch = 'aarch64'
            else:
                arch = 'x86_64'

            self.conf_info.update('tools.build:cxxflags', [
                '/clang:-nostdinc++',
                '/clang:-nostdlib++',
                '/imsvc', f'{self.package_folder}/include/c++/v1',
                '/imsvc', f'{self.package_folder}/include/{arch}-pc-windows-msvc/c++/v1',
            ])
            self.conf_info.update('tools.build:defines', ['-D_CRT_STDIO_ISO_WIDE_SPECIFIERS'])

            major_version = Version(self.version).major

            link_flags = [
                f'{self.package_folder}/lib/{arch}-pc-windows-msvc/libc++.lib',
                f'{self.package_folder}/lib/clang/{major_version}/lib/{arch}-pc-windows-msvc/clang_rt.builtins.lib',
                'vcruntime.lib',
                'msvcprt.lib'
            ]
            self.conf_info.update('tools.build:exelinkflags', link_flags)
            self.conf_info.update('tools.build:sharedlinkflags', link_flags)

            self.conf_info.update(
                'user.microblink.cmaketoolchain:cache_variables',
                {'MB_LLVM_ROOT': self.package_folder}
            )

    # ------------------------------------------------------------------------------
    # helper methods
    # ------------------------------------------------------------------------------

    def _tool_name(self, tool):
        return f'{tool}.exe'

    def _define_tool_var(self, value):
        bin_folder = os.path.join(self.package_folder, 'bin')
        path = os.path.join(bin_folder, self._tool_name(value))
        return path

# pylint: skip-file
