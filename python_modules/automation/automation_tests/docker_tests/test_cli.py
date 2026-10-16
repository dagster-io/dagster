import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from automation.docker.cli import cli
from automation.docker.image_defs import get_image
from click.testing import CliRunner


@pytest.mark.parametrize("name", ["dagster-k8s", "dagster-celery-k8s", "user-code-example"])
@pytest.mark.parametrize("set_latest", [False, True])
@pytest.mark.parametrize(
    "platform_options,platforms",
    [
        ([], ["linux/amd64", "linux/arm64"]),
        (["--platform", "linux/arm64"], ["linux/arm64"]),
        (
            ["--platform", "linux/amd64", "--platform", "linux/arm64"],
            ["linux/amd64", "linux/arm64"],
        ),
    ],
)
def test_build_and_push_dockerhub(name, set_latest, platform_options, platforms):
    with patch("automation.docker.dagster_docker.execute_docker_buildx_build_and_push") as build:
        result = CliRunner().invoke(
            cli,
            [
                "build-and-push-dockerhub",
                "--name",
                name,
                "--dagster-version",
                "1.2.3",
                *(["--set-latest"] if set_latest else []),
                *platform_options,
            ],
        )
    assert result.exit_code == 0, result.output or str(result.exception)
    build.assert_called_once()
    args = build.call_args.kwargs
    assert args["platforms"] == platforms
    assert args["tags"] == [f"dagster/{name}:1.2.3"] + (
        [f"dagster/{name}:latest"] if set_latest else []
    )
    assert args["docker_args"]["DAGSTER_VERSION"] == "1.2.3"
    assert args["cwd"] == get_image(name).path


@pytest.mark.parametrize("exit_code", [0, 1])
def test_publish_example_build_context(monkeypatch, exit_code):
    image = get_image("user-code-example")
    last_updated = Path(image.path, "last_updated.yaml").read_bytes()
    calls = []

    def build(args, **kwargs):
        calls.append(args)
        assert kwargs["cwd"] == image.path
        assert Path(image.path, "build_cache", "deploy_k8s").is_dir()
        return exit_code

    monkeypatch.setattr(subprocess, "call", build)
    result = CliRunner().invoke(
        cli,
        ["build-and-push-dockerhub", "--name", image.image, "--dagster-version", "1.2.3"],
    )
    assert result.exit_code == exit_code, result.output or str(result.exception)
    assert len(calls) == 1
    assert calls[0][:4] == ["docker", "buildx", "build", "."]
    assert "--push" in calls[0]
    assert not Path(image.path, "build_cache").exists()
    assert Path(image.path, "last_updated.yaml").read_bytes() == last_updated
