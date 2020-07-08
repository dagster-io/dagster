''' Use this script to build all unit images locally
from the snapshot requirement files in .buildkite/images/unit
'''
from defines import UNIT_IMAGE_VERSION, SupportedPythons
from images.unit.image_build import execute_image_build

if __name__ == '__main__':
    for python_version in SupportedPythons:
        execute_image_build(
            python_version=python_version, image_version=UNIT_IMAGE_VERSION,
        )
