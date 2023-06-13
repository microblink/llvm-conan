from conan import ConanFile
from conan.tools.cmake import cmake_layout, CMake
import os


class TestPackageConan(ConanFile):
    settings = "os", "build_type", "arch", "compiler"
    generators = "CMakeToolchain", "VCVars"

    def requirements(self):
        self.tool_requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self, generator='Ninja')
        cmake.configure()
        cmake.build()

    def test(self):
        os.chdir('bin')
        self.run('.{}test_package{}'.format(os.sep, '.exe' if self.settings.os == 'Windows' else ''))
        self.run('.{}test_package_libcxx{}'.format(os.sep, '.exe' if self.settings.os == 'Windows' else ''))

# pylint: skip-file
