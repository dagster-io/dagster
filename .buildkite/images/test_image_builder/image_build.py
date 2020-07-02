import os

from automation.images import local_test_builder_image


def image_build():
    # always set cwd to the directory where the file lives
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.system('docker build . -t ' + local_test_builder_image())


if __name__ == '__main__':
    image_build()
