from conans import ConanFile, tools
import os
import shutil


# NOTE: For building armv8 version, initialize vcvars with amd64_arm64 profile and invoke
# with conan params: -s os_build=Windows -s arch_build=armv8 -s compiler=clang -s compiler.version=<version>
# for x86_64, just use -s arch_build=x86_64
class LLVMConan(ConanFile):
    name = "llvm"
    version = "14.0.6"
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

    def build_requirements(self):
        if self._host_arch == 'x86_64':
            self.build_requires('7zip/19.00')

    def source(self):
        self.run(f'git clone --depth 1 --branch llvmorg-{self.version} https://github.com/llvm/llvm-project')

    def build(self):
        # download binaries here in the build function in order to support building both ARM and x64 version on
        # single (ARM) machine (using Microsoft's emulation layer)
        if self._host_arch == 'x86_64':
            download_url = f'https://github.com/llvm/llvm-project/releases/download/llvmorg-{self.version}/' + \
                           f'LLVM-{self.version}-win64.exe'
            filename = 'llvm.exe'
        else:
            download_url = f'https://github.com/llvm/llvm-project/releases/download/llvmorg-{self.version}' + \
                           f'/LLVM-{self.version}-woa64.zip'
            filename = 'llvm.zip'

        tools.download(download_url, filename)

        os.mkdir('llvm-bin')
        with tools.chdir('llvm-bin'):
            if self._host_arch == 'x86_64':
                self.output.info('Extracting llvm.exe...')
                self.run('7z x ../llvm.exe')
                shutil.rmtree('$PLUGINSDIR')
                os.unlink('Uninstall.exe')
            else:
                self.output.info('Extracting llvm.zip...')
                tools.unzip('../llvm.zip')

        cmake_parameters = [
            'cmake',
            '-GNinja',
            '-DCMAKE_BUILD_TYPE=Release',
            '-DLLVM_ENABLE_RUNTIMES="libcxx"',
            '-DLLVM_ENABLE_LTO=Thin',
            '-DLIBCXX_ABI_VERSION=2',
            '-DLIBCXX_ABI_UNSTABLE=ON',
            '-DLIBCXX_ENABLE_EXCEPTIONS=OFF',
            '-DLIBCXX_ENABLE_RTTI=ON',
            '-DLIBCXX_ENABLE_SHARED=OFF',
            '-DLIBCXX_ENABLE_FILESYSTEM=ON',
            '-DCMAKE_C_FLAGS="-fsplit-lto-unit"',
            '-DCMAKE_CXX_FLAGS="-fsplit-lto-unit"',
            '-DCMAKE_INSTALL_PREFIX=../llvm-install',
        ]

        with tools.environment_append({
            'CC': os.path.join(self.build_folder, 'llvm-bin', 'bin', self._tool_name('clang-cl' if self.options.use_clang_cl else 'clang')),     # noqa: E501
            'CXX': os.path.join(self.build_folder, 'llvm-bin', 'bin', self._tool_name('clang-cl' if self.options.use_clang_cl else 'clang++')),  # noqa: E501
            'AR': os.path.join(self.build_folder, 'llvm-bin', 'bin', self._tool_name('llvm-ar')),
            'RANLIB': os.path.join(self.build_folder, 'llvm-bin', 'bin', self._tool_name('llvm-ranlib')),
            'NM': os.path.join(self.build_folder, 'llvm-bin', 'bin', self._tool_name('llvm-nm')),
                }):

            os.mkdir('libcxx-build')
            with tools.chdir('libcxx-build'):
                cmake_invocation = ' '.join(cmake_parameters + [f'{self.source_folder}/llvm-project/runtimes'])

                self.run(cmake_invocation)
                self.run('ninja cxx')
                self.run('ninja install-cxx')

    def package(self):
        self.copy('*', src='llvm-bin')
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
