# ruff: noqa: T201
import subprocess
import sys
from datetime import datetime, timezone
from typing import Optional

import dagster._check as check


def execute_docker_build(
    image: str,
    docker_args: Optional[dict[str, str]] = None,
    cwd: Optional[str] = None,
    platform: Optional[str] = None,
):
    check.str_param(image, "image")
    docker_args = check.opt_dict_param(docker_args, "docker_args", key_type=str, value_type=str)
    cwd = check.opt_str_param(cwd, "cwd")

    print(f"Building image {image}")

    args = ["docker", "build", "."]

    for arg, value in docker_args.items():
        args += ["--build-arg", f"{arg}={value}"]

    args += ["-t", image]
    args += ["--progress", "plain"]

    if platform:
        args += ["--platform", platform]

    print(" ".join(args))

    retval = subprocess.call(args, stderr=sys.stderr, stdout=sys.stdout, cwd=cwd)
    check.invariant(retval == 0, "Process must exit successfully")


def execute_docker_push(image: str) -> None:
    check.str_param(image, "image")

    print(f"Pushing image {image}")
    retval = subprocess.call(["docker", "push", image], stderr=sys.stderr, stdout=sys.stdout)
    check.invariant(retval == 0, "docker push must succeed")


def execute_docker_tag(local_image: str, remote_image: str) -> None:
    """Re-tag an existing image."""
    check.str_param(local_image, "local_image")
    check.str_param(remote_image, "remote_image")

    print(f"Tagging local image {local_image} as remote image {remote_image}")
    retval = subprocess.call(
        ["docker", "tag", local_image, remote_image], stderr=sys.stderr, stdout=sys.stdout
    )
    check.invariant(retval == 0, "docker tag must succeed")


def python_version_image_tag(python_version: str, image_version: str) -> str:
    """Dagster images are typically tagged as py<PYTHON VERSION>-<IMAGE VERSION>."""
    check.str_param(python_version, "python_version")
    check.str_param(image_version, "image_version")
    return f"py{python_version}-{image_version}"


def current_time_str() -> str:
    """Should be UTC date string like 2020-07-11T035005."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
