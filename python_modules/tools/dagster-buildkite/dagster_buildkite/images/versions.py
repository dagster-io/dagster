import os

import yaml

from dagster_buildkite.defines import GIT_REPO_ROOT

def get_image_version(image_name: str) -> str:
    root_images_path = os.path.join(
        GIT_REPO_ROOT,
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


BUILDKITE_BUILD_TEST_PROJECT_IMAGE_IMAGE_VERSION: str = get_image_version(
    "buildkite-build-test-project-image"
)
BUILDKITE_COVERAGE_IMAGE_VERSION: str = get_image_version("buildkite-coverage")
BUILDKITE_TEST_IMAGE_VERSION: str = get_image_version("buildkite-test")
TEST_PROJECT_BASE_IMAGE_VERSION: str = get_image_version("test-project-base")
