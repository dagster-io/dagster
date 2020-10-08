import os
import subprocess
import sys

from dagster import check
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation import InProcessRepositoryLocation
from dagster.utils import file_relative_path, git_repository_root

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


def test_repo_path():
    return os.path.join(
        git_repository_root(), "python_modules", "dagster-test", "dagster_test", "test_project"
    )


def test_project_environments_path():
    return os.path.join(test_repo_path(), "environments")


def build_and_tag_test_image(tag):
    check.str_param(tag, "tag")

    base_python = "3.7.8"

    # Build and tag local dagster test image
    return subprocess.check_output(["./build.sh", base_python, tag], cwd=test_repo_path())


def get_test_project_recon_pipeline(pipeline_name):
    return ReconstructableRepository.for_file(
        file_relative_path(__file__, "test_pipelines/repo.py"), "define_demo_execution_repo",
    ).get_reconstructable_pipeline(pipeline_name)


def get_test_project_external_pipeline(pipeline_name):
    return (
        InProcessRepositoryLocation(
            ReconstructableRepository.for_file(
                file_relative_path(__file__, "test_pipelines/repo.py"),
                "define_demo_execution_repo",
            )
        )
        .get_repository("demo_execution_repo")
        .get_full_external_pipeline(pipeline_name)
    )


def test_project_docker_image():
    docker_repository = os.getenv("DAGSTER_DOCKER_REPOSITORY")
    image_name = os.getenv("DAGSTER_DOCKER_IMAGE", "dagster-docker-buildkite")
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

    # This needs to be a domain name to avoid the k8s machinery automatically prefixing it with
    # `docker.io/` and attempting to pull images from Docker Hub
    if not docker_repository:
        docker_repository = "dagster.io.priv"

    if not docker_image_tag:
        # Detect the python version we're running on
        majmin = str(sys.version_info.major) + str(sys.version_info.minor)

        docker_image_tag = "py{majmin}-{image_version}".format(
            majmin=majmin, image_version="latest"
        )

    final_docker_image = "{repository}/{image_name}:{tag}".format(
        repository=docker_repository, image_name=image_name, tag=docker_image_tag
    )
    print("Using Docker image: %s" % final_docker_image)  # pylint: disable=print-call
    return final_docker_image
