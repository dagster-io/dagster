import os

import yaml


# This should be an enum once we make our own buildkite AMI with py3
class SupportedPython:
    V3_8 = "3.8.3"
    V3_7 = "3.7.8"
    V3_6 = "3.6.11"


SupportedPythons = [
    SupportedPython.V3_6,
    SupportedPython.V3_7,
    SupportedPython.V3_8,
]


TOX_MAP = {
    SupportedPython.V3_8: "py38",
    SupportedPython.V3_7: "py37",
    SupportedPython.V3_6: "py36",
}

####################################################################################################
# Dagster images
#
# These timestamps are generated with:
# datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%S")
####################################################################################################
def get_image_version(image_name):
    root_images_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "..",
        "python_modules",
        "automation",
        "automation",
        "docker",
        "images",
    )
    with open(os.path.join(root_images_path, image_name, "last_updated.yaml")) as f:
        versions = set(yaml.safe_load(f).values())

    # There should be only one image timestamp tag across all Python versions
    assert len(versions) == 1
    return versions.pop()


INTEGRATION_IMAGE_VERSION = get_image_version("buildkite-integration")
UNIT_IMAGE_VERSION = get_image_version("buildkite-unit")
