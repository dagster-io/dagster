import os
from typing import Optional

import yaml
from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import CommandStepBuilder


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


BUILDKITE_BUILD_TEST_PROJECT_IMAGE_IMAGE_VERSION: str = get_image_version(
    "buildkite-build-test-project-image"
)
BUILDKITE_TEST_IMAGE_VERSION: str = get_image_version("buildkite-test")
TEST_PROJECT_BASE_IMAGE_VERSION: str = get_image_version("test-project-base")


def add_test_image(
    step_builder: CommandStepBuilder,
    ver: AvailablePythonVersion,
    env: Optional[list[str]] = None,
) -> CommandStepBuilder:
    return step_builder.on_python_image(
        image=f"buildkite-test:py{ver.value}-{BUILDKITE_TEST_IMAGE_VERSION}",
        env=env,
    ).with_ecr_login()
