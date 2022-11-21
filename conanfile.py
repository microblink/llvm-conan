from conans import ConanFile, tools
import os

# Package build instructions:
# - initialize your terminal with vcvars
# - set cc and cxx to clang-cl of the previous version of clang, that will be used for building the new package
# - run following command:
# conan create . microblink/stable -pr clang-windows-generic-x64 -s compiler.version=<version-used-for-building> -tf=None


class LLVMConan(ConanFile):
    name = "llvm"
    version = "15.0.5"
    url = "https://github.com/microblink/llvm-conan"
    license = "Apache 2.0 WITH LLVM-exception"
    description = "LLVM toolchain with custom build of libc++"
    topics = ('llvm', 'compiler')
    settings = {
        "os_build": ['Windows'],
        "arch_build": ['x86_64', 'armv8']
    }
    no_copy_source = True
    options = {
        'use_clang_cl': [True, False]
    }

    # forward compatibility for conan v2.0 when we ditch os_build and arch_build
    @property
    def _host_arch(self):
        return self.settings.arch_build

    @property
    def _host_os(self):
        return self.settings.os_build

    def config_options(self):
        self.options.use_clang_cl = self.settings.os_build == 'Windows'

    def source(self):
        self.run(
            f'git clone --depth 1 --branch microblink-llvmorg-{self.version} https://github.com/microblink/llvm-project'
        )

    def build(self):

        additional_cc_flags = '/clang:-Ofast'
        if self._host_arch == 'x86_64':
            additional_cc_flags += ' /clang:-mavx /clang:-mavx2 /clang:-mfma'

        cmake_parameters = [
            'cmake',
            '-GNinja',
            '-DCMAKE_BUILD_TYPE=Release',
            '-DLLVM_ENABLE_PROJECTS="clang;lld;lldb;compiler-rt"',
            '-DLLVM_ENABLE_RUNTIMES="libcxx"',
            '-DLLVM_ENABLE_LTO=Thin',
            '-DLLVM_PARALLEL_LINK_JOBS=3',
            '-DLLVM_USE_LINKER="lld"',
            '-DLLVM_ENABLE_EH=OFF',
            '-DLLVM_ENABLE_RTTI=OFF',
            # '-DLLVM_BUILD_LLVM_DYLIB=ON',
            # '-DLLVM_LINK_LLVM_DYLIB=ON',
            # '-DLLVM_ENABLE_PER_TARGET_RUNTIME_DIR=ON',
            '-DLLVM_INCLUDE_TESTS=OFF',
            '-DLLVM_INCLUDE_BENCHMARKS=OFF',
            '-DCLANG_DEFAULT_LINKER=lld',
            '-DCLANG_DEFAULT_RTLIB=compiler-rt',
            '-DLIBCXX_USE_COMPILER_RT=YES',
            '-DLIBCXX_ABI_VERSION=2',
            '-DLIBCXX_ABI_UNSTABLE=ON',
            '-DLIBCXX_ENABLE_EXCEPTIONS=OFF',
            '-DLIBCXX_ENABLE_RTTI=ON',
            '-DLIBCXX_ENABLE_SHARED=OFF',
            '-DLIBCXX_ENABLE_FILESYSTEM=ON',
            '-DLIBCXX_INCLUDE_BENCHMARKS=OFF',
            '-DLIBCXX_INCLUDE_TESTS=OFF,'
            '-DLIBCXX_INCLUDE_DOCS=OFF',
            f'-DCMAKE_C_FLAGS="-fsplit-lto-unit {additional_cc_flags}"',
            f'-DCMAKE_CXX_FLAGS="-fsplit-lto-unit {additional_cc_flags}"',
            '-DCMAKE_INSTALL_PREFIX=../llvm-install',
        ]

        os.mkdir('llvm-build')
        with tools.chdir('llvm-build'):
            cmake_invocation = ' '.join(cmake_parameters + [f'{self.source_folder}/llvm-project/llvm'])

            self.run(cmake_invocation)
            self.run('ninja')
            self.run('ninja install')

    def package(self):
        self.copy('*', src='llvm-install')
        self.copy('libcxx_windows.cmake')

    def package_id(self):
        del self.info.options.use_clang_cl

    def _tool_name(self, tool):
        suffix = '.exe' if self.settings.os_build == 'Windows' else ''
        return f'{tool}{suffix}'

    def _define_tool_var(self, name, value):
        bin_folder = os.path.join(self.package_folder, 'bin')
        path = os.path.join(bin_folder, self._tool_name(value))
        self.output.info('Creating %s environment variable: %s' % (name, path))
        return path

    def package_info(self):
        self.env_info.CC = self._define_tool_var('CC', 'clang-cl' if self.options.use_clang_cl else 'clang')
        self.env_info.CXX = self._define_tool_var('CXX', 'clang-cl' if self.options.use_clang_cl else 'clang++')  # noqa: E501

        # NOTE: for statically linking the libc++ only (by default, MS STL is used)
        # cxxflags = [
        #    '-nostdinc++',
        #    '-nostdlib++',
        #    '-isystem',
        #    f'{self.package_folder}/include/c++/v1',
        #    '-D_CRT_STDIO_ISO_WIDE_SPECIFIERS'
        # ]
        # if self.settings.os_build == 'Windows':
        #     self.env_info.CXXFLAGS = ' '.join([f'/clang:{x}' for x in cxxflags])
        #     # for static linking
        #     self.env_info.LDFLAGS = f'/nodefaultlib {self.package_folder}/lib/libc++.lib ucrt.lib libcmt.lib iso_stdio_wide_specifiers.lib libvcruntime.lib msvcprt.lib'  # noqa: E501
        # else:
        #     self.env_info.CXXFLAGS = ' '.join(cxxflags)
        #     self.env_info.LDFLAGS = f'-L {self.package_folder}/lib -lc++'

        self.env_info.LD = self._define_tool_var('LD', 'lld-link' if self.settings.os_build == 'Windows' else 'lld')
        self.env_info.AR = self._define_tool_var('AR', 'llvm-ar')
        self.env_info.RANLIB = self._define_tool_var('RANLIB', 'llvm-ranlib')
        self.env_info.STRIP = self._define_tool_var('STRIP', 'llvm-strip')
        self.env_info.NM = self._define_tool_var('NM', 'llvm-nm')
        self.env_info.OBJCOPY = self._define_tool_var('OBJCOPY', 'llvm-objcopy')
        self.env_info.OBJDUMP = self._define_tool_var('OBJDUMP', 'ollvm-bjdump')
        self.env_info.READELF = self._define_tool_var('READOBJ', 'llvm-readobj')
