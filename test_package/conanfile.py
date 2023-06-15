from conan import ConanFile
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain


class TestPackageConan(ConanFile):
    settings = "os", "build_type", "arch", "compiler"
    generators = "VCVars"

    def requirements(self):
        self.tool_requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def generate(self):
        cmake = CMakeToolchain(self)
        if self.settings.compiler.libcxx == 'libc++v2':
            cmake.cache_variables['SHOULD_USE_LIBCXX'] = True
        cmake.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        self.run('.\\test_package.exe')

# pylint: skip-file
