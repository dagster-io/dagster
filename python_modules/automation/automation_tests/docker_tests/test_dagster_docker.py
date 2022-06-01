import os
from pathlib import Path

from automation.docker.dagster_docker import DagsterDockerImage


def test_image_path():
    # dagster/python_modules/automation/docker/images
    default_images_path = os.path.join(
        Path(__file__).parents[2],
        "automation",
        "docker",
        "images",
    )
    assert DagsterDockerImage("foo", default_images_path).path == os.path.join(
        default_images_path, "foo"
    )
