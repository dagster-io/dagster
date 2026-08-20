import os
import subprocess
from pathlib import Path

from automation.docker.dagster_docker import DagsterDockerImage
from automation.docker.utils import execute_docker_buildx_build_and_push


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


def test_buildx_build_and_push_builds_one_manifest_list(monkeypatch):
    recorded = []

    def fake_call(args, **_kwargs):
        recorded.append(args)
        return 0

    monkeypatch.setattr(subprocess, "call", fake_call)

    execute_docker_buildx_build_and_push(
        tags=["dagster/dagster-k8s:1.2.3", "dagster/dagster-k8s:latest"],
        platforms=["linux/amd64", "linux/arm64"],
        docker_args={"DAGSTER_VERSION": "1.2.3"},
    )

    # One buildx invocation, not build/tag/push: the latter would leave each tag holding
    # only the last architecture built.
    assert len(recorded) == 1
    args = recorded[0]

    assert args[:4] == ["docker", "buildx", "build", "."]
    assert args[args.index("--platform") + 1] == "linux/amd64,linux/arm64"
    assert args[args.index("--build-arg") + 1] == "DAGSTER_VERSION=1.2.3"
    assert "--push" in args
    assert args.count("-t") == 2
