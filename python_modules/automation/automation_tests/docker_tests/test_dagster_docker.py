import os
import subprocess
from pathlib import Path

import pytest
from automation.docker.dagster_docker import DagsterDockerImage
from automation.docker.utils import execute_docker_buildx_build_and_push
from dagster._check import CheckError


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


@pytest.mark.parametrize("exit_code", [0, 1])
@pytest.mark.parametrize("has_local_image", [False, True])
def test_multiplatform_publish_preserves_local_image_metadata(
    tmp_path, monkeypatch, exit_code, has_local_image
):
    image_path = tmp_path / "test-image"
    image_path.mkdir()
    (image_path / "versions.yaml").write_text(
        '"3.10":\n  docker_args:\n    BASE_IMAGE: python:3.10-slim\n'
    )
    last_updated = image_path / "last_updated.yaml"
    original = '"3.10": local-build\n'
    if has_local_image:
        last_updated.write_text(original)
    image = DagsterDockerImage("test-image", images_path=str(tmp_path))
    monkeypatch.setattr(subprocess, "call", lambda *_args, **_kwargs: exit_code)

    def publish():
        image.build_and_push_multiplatform(
            "1.2.3", "3.10", ["example/image:1.2.3"], ["linux/amd64", "linux/arm64"]
        )

    if exit_code:
        with pytest.raises(CheckError, match="Process must exit successfully"):
            publish()
    else:
        publish()

    if has_local_image:
        assert last_updated.read_text() == original
        assert image.local_image("3.10") == "dagster/test-image:py3.10-local-build"
    else:
        assert not last_updated.exists()
