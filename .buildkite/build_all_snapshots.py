''' Use this script to refresh all snapshot requirements files
Updated requirements files are in .buildkite/images/integration
'''
from defines import INTEGRATION_BASE_VERSION, SupportedPythons
from images.integration_snapshot_builder.image_build import execute_build_image

if __name__ == '__main__':
    for python_version in SupportedPythons:
        execute_build_image(
            python_version=python_version, base_image_version=INTEGRATION_BASE_VERSION,
        )
