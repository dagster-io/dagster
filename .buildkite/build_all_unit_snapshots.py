''' Use this script to refresh all snapshot requirements files
Updated requirements files are in .buildkite/images/unit
'''
from defines import UNIT_IMAGE_VERSION, SupportedPythons
from images.unit_snapshot_builder.image_build import execute_build_image

if __name__ == '__main__':
    for python_version in SupportedPythons:
        execute_build_image(
            python_version=python_version, base_image_version=UNIT_IMAGE_VERSION,
        )
