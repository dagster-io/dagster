'''Wraps access to the test project at .buildkite/images/docker/test_project for Docker/K8s tests.

This file is also imported by dagster-airflow tests.
'''

import os
import subprocess
import sys

from dagster import check
from dagster.utils import git_repository_root

IS_BUILDKITE = os.getenv('BUILDKITE') is not None


def test_repo_path():
    return os.path.join(git_repository_root(), '.buildkite', 'images', 'docker', 'test_project')


def test_project_environments_path():
    return os.path.join(test_repo_path(), 'test_pipelines', 'environments')


def build_and_tag_test_image(tag):
    check.str_param(tag, 'tag')

    base_python = '.'.join(
        [str(x) for x in [sys.version_info.major, sys.version_info.minor, sys.version_info.micro]]
    )

    # Build and tag local dagster test image
    return subprocess.check_output(['./build.sh', base_python, tag], cwd=test_repo_path())


def test_project_docker_image():
    docker_repository = os.getenv('DAGSTER_DOCKER_REPOSITORY')
    image_name = os.getenv('DAGSTER_DOCKER_IMAGE', 'dagster-docker-buildkite')
    docker_image_tag = os.getenv('DAGSTER_DOCKER_IMAGE_TAG')

    if IS_BUILDKITE:
        assert docker_image_tag is not None, (
            'This test requires the environment variable DAGSTER_DOCKER_IMAGE_TAG to be set '
            'to proceed'
        )
        assert docker_repository is not None, (
            'This test requires the environment variable DAGSTER_DOCKER_REPOSITORY to be set '
            'to proceed'
        )

    # This needs to be a domain name to avoid the k8s machinery automatically prefixing it with
    # `docker.io/` and attempting to pull images from Docker Hub
    if not docker_repository:
        docker_repository = 'dagster.io.priv'

    if not docker_image_tag:
        # Detect the python version we're running on
        majmin = str(sys.version_info.major) + str(sys.version_info.minor)

        docker_image_tag = 'py{majmin}-{image_version}'.format(
            majmin=majmin, image_version='latest'
        )

    final_docker_image = '{repository}/{image_name}:{tag}'.format(
        repository=docker_repository, image_name=image_name, tag=docker_image_tag
    )
    print('Using Docker image: %s' % final_docker_image)
    return final_docker_image
