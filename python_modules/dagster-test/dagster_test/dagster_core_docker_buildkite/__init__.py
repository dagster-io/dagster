import os
import subprocess
import sys

from dagster import check
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation import InProcessRepositoryLocationOrigin
from dagster.utils import file_relative_path, git_repository_root

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


def get_test_repo_path():
    return os.path.join(
        git_repository_root(),
        "python_modules",
        "dagster-test",
        "dagster_test",
        "dagster_core_docker_buildkite",
    )


def get_test_project_environments_path():
    return os.path.join(get_test_repo_path(), "environments")


def build_and_tag_test_image(tag):
    check.str_param(tag, "tag")

    base_python = ".".join(
        [str(x) for x in [sys.version_info.major, sys.version_info.minor, sys.version_info.micro]]
    )

    # Build and tag local dagster test image
    return subprocess.check_output(
        ["../../build_core.sh", base_python, tag],
        cwd=get_test_repo_path(),
        stderr=subprocess.STDOUT,
    )


def get_test_project_external_pipeline(pipeline_name):
    return (
        InProcessRepositoryLocationOrigin(
            ReconstructableRepository.for_file(
                file_relative_path(__file__, "test_pipelines/repo.py"),
                "define_demo_execution_repo",
            )
        )
        .create_handle()
        .create_location()
        .get_repository("demo_execution_repo")
        .get_full_external_pipeline(pipeline_name)
    )


def get_default_docker_image_tag():
    # Detect the python version we're running on
    majmin = str(sys.version_info.major) + str(sys.version_info.minor)

    return "py{majmin}-{image_version}".format(majmin=majmin, image_version="latest")


def get_test_project_docker_image():
    docker_repository = os.getenv("DAGSTER_DOCKER_REPOSITORY")
    image_name = os.getenv("DAGSTER_DOCKER_IMAGE", "buildkite-test-image-core")
    docker_image_tag = os.getenv("DAGSTER_DOCKER_IMAGE_TAG")

    if IS_BUILDKITE:
        assert docker_image_tag is not None, (
            "This test requires the environment variable DAGSTER_DOCKER_IMAGE_TAG to be set "
            "to proceed"
        )
        assert docker_repository is not None, (
            "This test requires the environment variable DAGSTER_DOCKER_REPOSITORY to be set "
            "to proceed"
        )

    if not docker_image_tag:
        docker_image_tag = get_default_docker_image_tag()

    final_docker_image = "{repository}{image_name}:{tag}".format(
        repository="{}/".format(docker_repository) if docker_repository else "",
        image_name=image_name,
        tag=docker_image_tag,
    )
    print("Using Docker image: %s" % final_docker_image)  # pylint: disable=print-call
    return final_docker_image
