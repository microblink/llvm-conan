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
# conan create . --user microblink --channel stable --build-require -pr clang-<new-version>-windows -pr:b clang-<current-version>-windows


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
                'LLVM_ENABLE_PROJECTS': 'clang;lld;lldb;compiler-rt;polly',
                'LLVM_ENABLE_RUNTIMES': 'libcxx',
                'LLVM_TARGETS_TO_BUILD': 'AArch64;ARM;WebAssembly;X86',
                'LLVM_ENABLE_LTO': 'Thin',
                'LLVM_PARALLEL_LINK_JOBS': '3',
                'LLVM_USE_LINKER': 'lld',
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
        # cannot use foundation, so need to include it's implementation here
        # see https://github.com/conan-io/conan/issues/14085
        self._mb_setup_lto()
        self._mb_setup_sanitizers()

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

        if self.settings_target.compiler.libcxx == 'libc++v2':
            if self.settings_target.arch == 'armv8':
                arch = 'aarch64'
            else:
                arch = 'x86_64'

            sanitized_package_folder = self.package_folder.replace('\\', '/')

            self.conf_info.append('tools.build:cxxflags', [
                '/clang:-nostdinc++',
                '/clang:-nostdlib++',
                f'/I{sanitized_package_folder}/include/c++/v1',
                f'/I{sanitized_package_folder}/include/{arch}-pc-windows-msvc/c++/v1',
            ])
            self.conf_info.append('tools.build:defines', ['_CRT_STDIO_ISO_WIDE_SPECIFIERS'])

            major_version = Version(self.version).major

            link_flags = [
                f'{sanitized_package_folder}/lib/{arch}-pc-windows-msvc/libc++.lib',
                f'{sanitized_package_folder}/lib/clang/{major_version}/lib/{arch}-pc-windows-msvc/clang_rt.builtins.lib',
                'vcruntime.lib',
                'msvcprt.lib'
            ]
            self.conf_info.append('tools.build:exelinkflags', link_flags)
            self.conf_info.append('tools.build:sharedlinkflags', link_flags)

            self.conf_info.update(
                'user.microblink.cmaketoolchain:cache_variables',
                {'MB_LLVM_ROOT': sanitized_package_folder}
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

    # ------------------------------------------------------------------------------
    # copied from foundation package as a workaround for
    # https://github.com/conan-io/conan/issues/14085
    # ------------------------------------------------------------------------------
    def _mb_setup_lto(self):
        lto = self.settings_target.get_safe('compiler.link_time_optimization')
        if lto is not None:
            lto_enabled = bool(lto)
        else:
            lto_enabled = self.settings_target.build_type == 'Release'

        if lto_enabled:
            cflags = []
            lflags = []
            if self.settings_target.compiler in ['clang', 'apple-clang']:
                cflags = ['-flto=thin']
                lflags = ['-flto=thin']
            elif self.settings_target.compiler == 'msvc':
                cflags = ['-GL']
                lflags = ['-LTCG']
            else:
                cflags = ['-flto']
                lflags = ['-flto']

            self.conf_info.append('tools.build:cflags', cflags)
            self.conf_info.append('tools.build:cxxflags', cflags)
            self.conf_info.append('tools.build:sharedlinkflags', lflags)
            self.conf_info.append('tools.build:exelinkflags', lflags)

            self.cpp_info.cflags.extend(cflags)
            self.cpp_info.cxxflags.extend(cflags)
            self.cpp_info.sharedlinkflags.extend(lflags)
            self.cpp_info.exelinkflags.extend(lflags)

    def _mb_setup_sanitizers(self):
        runtime_check_flags = []

        if self.settings_target.compiler in ['clang', 'apple-clang']:
            sanitizers = self.settings_target.get_safe('compiler.sanitizers')
            if sanitizers is None:
                if self.settings_target.build_type in ['Debug', 'DevRelease'] \
                        and self.settings_target.os in ['Macos', 'Linux']:
                    sanitizers = "ASan+UBSan"
                else:
                    sanitizers = "disabled"

            if sanitizers == "ASan+UBSan":
                # runtime checks are enabled, so we need to add ASAN/UBSAN linker flags
                runtime_check_flags = ['-fsanitize=undefined', '-fsanitize=address', '-fsanitize=integer']
            elif sanitizers == "TSan":
                runtime_check_flags = ['-fsanitize=thread']
            elif sanitizers == "MSan":
                runtime_check_flags = ['-fsanitize=memory']
            elif sanitizers == 'CFISan':
                runtime_check_flags = ['-fsanitize=cfi']

        if self.settings_target.compiler == 'msvc':
            sanitizers = self.settings_target.get_safe('compiler.sanitizers')
            if sanitizers is None:
                if self.settings_target.build_type in ['Debug', 'DevRelease']:
                    sanitizers = "ASan+UBSan"
                else:
                    sanitizers = "disabled"

            if sanitizers == 'ASan':
                runtime_check_flags = ['-fsanitize=address']

        self.cpp_info.cflags.extend(runtime_check_flags)
        self.cpp_info.cxxflags.extend(runtime_check_flags)
        self.cpp_info.sharedlinkflags.extend(runtime_check_flags)
        self.cpp_info.exelinkflags.extend(runtime_check_flags)

        self.conf_info.append('tools.build:cflags', runtime_check_flags)
        self.conf_info.append('tools.build:cxxflags', runtime_check_flags)
        self.conf_info.append('tools.build:sharedlinkflags', runtime_check_flags)
        self.conf_info.append('tools.build:exelinkflags', runtime_check_flags)

# pylint: skip-file
