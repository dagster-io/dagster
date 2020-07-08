from defines import UNIT_IMAGE_VERSION, SupportedPythons
from images.unit.image_push import execute_image_push

if __name__ == '__main__':
    for python_version in SupportedPythons:
        execute_image_push(python_version=python_version, image_version=UNIT_IMAGE_VERSION)
