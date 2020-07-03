'''Just for local development. Not used to build in buildkite pipeline'''
from defines import INTEGRATION_BASE_VERSION, SupportedPythons
from images.integration.image_push import execute_image_push

if __name__ == '__main__':
    for python_version in SupportedPythons:
        execute_image_push(python_version=python_version, image_version=INTEGRATION_BASE_VERSION)
