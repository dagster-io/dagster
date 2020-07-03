'''Just for local development. Not used to build in buildkite pipelines'''
from defines import INTEGRATION_BASE_VERSION, SupportedPythons
from images.integration_base.image_build import execute_image_build

if __name__ == '__main__':
    for python_version in SupportedPythons:
        execute_image_build(python_version=python_version, image_version=INTEGRATION_BASE_VERSION)
