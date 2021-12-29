from conans import ConanFile, CMake
import os


class TestPackageConan(ConanFile):
    settings = "os", "build_type", "arch", "compiler"
    generators = "cmake"

    def build(self):
        cmake = CMake(self, generator='Ninja')
        cmake.configure()
        cmake.build()

    def test(self):
        os.chdir('bin')
        self.run('.{}test_package{}'.format(os.sep, '.exe' if self.settings.os == 'Windows' else ''))
