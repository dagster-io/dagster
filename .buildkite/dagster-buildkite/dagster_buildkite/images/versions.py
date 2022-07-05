import os

import yaml


def get_image_version(image_name: str) -> str:
    root_images_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "..",
        "..",
        "..",
        "..",
        "python_modules",
        "automation",
        "automation",
        "docker",
        "images",
    )
    with open(
        os.path.join(root_images_path, image_name, "last_updated.yaml"), encoding="utf8"
    ) as f:
        versions = set(yaml.safe_load(f).values())

    # There should be only one image timestamp tag across all Python versions
    assert len(versions) == 1
    return versions.pop()


COVERAGE_IMAGE_VERSION: str = get_image_version("buildkite-coverage")
INTEGRATION_IMAGE_VERSION: str = get_image_version("buildkite-integration")
TEST_IMAGE_BUILDER_BASE_VERSION: str = get_image_version("buildkite-test-image-builder-base")
TEST_IMAGE_BUILDER_VERSION: str = get_image_version("buildkite-test-image-builder")
