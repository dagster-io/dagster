from typing import List, Optional

import click
import dagster._check as check

from .dagster_docker import DagsterDockerImage
from .ecr import ensure_ecr_login
from .image_defs import get_image, list_images
from .utils import current_time_str, execute_docker_push, execute_docker_tag

CLI_HELP = """This CLI is used for building the various Dagster images we use in test
"""

AWS_ECR_REGISTRY = "public.ecr.aws/dagster"


@click.group(help=CLI_HELP)
def cli():
    pass


@cli.command()
def list():  # pylint: disable=redefined-builtin
    for image in list_images():
        print(image.image)  # noqa: T201


# Shared options between `build` and `build_all`
opt_build_name = click.option("--name", required=True, help="Name of image to build")
opt_build_dagster_version = click.option(
    "--dagster-version",
    required=True,
    help="Version of image to build",
)
opt_build_platform = click.option(
    "--platform",
    required=False,
    help="Target platform name to pass to `docker build`",
)
opt_build_timestamp = click.option(
    "-t",
    "--timestamp",
    type=click.STRING,
    required=False,
    default=current_time_str(),
    help="Timestamp to build in format 2020-07-11T040642 (defaults to now UTC)",
)


@cli.command()
@opt_build_name
@opt_build_dagster_version
@opt_build_timestamp
@click.option("-v", "--python-version", type=click.STRING, required=True)
@opt_build_platform
def build(
    name: str, dagster_version: str, timestamp: str, python_version: str, platform: Optional[str]
):
    get_image(name).build(timestamp, dagster_version, python_version, platform)


@cli.command()
@opt_build_name
@opt_build_dagster_version
@opt_build_timestamp
@opt_build_platform
def build_all(name: str, dagster_version: str, timestamp: str, platform: Optional[str]):
    """Build all supported python versions for image."""
    image = get_image(name)

    for python_version in image.python_versions:
        image.build(timestamp, dagster_version, python_version, platform)


# Shared push options
opt_push_name = click.option("--name", required=True, help="Name of image to push")
opt_push_dagster_version = click.option(
    "--dagster-version",
    required=True,
    help="Version of image to push",
)
opt_set_latest = click.option(
    "--set-latest",
    is_flag=True,
    default=False,
    help="Whether to tag the image as latest",
)


@cli.command()
@opt_push_name
@click.option("-v", "--python-version", type=click.STRING, required=True)
@click.option("--custom-tag", type=click.STRING, required=False)
def push(name: str, python_version: str, custom_tag: Optional[str]):
    ensure_ecr_login()
    get_image(name).push(python_version, custom_tag=custom_tag)


@cli.command()
@opt_push_name
def push_all(name: str):
    ensure_ecr_login()
    image = get_image(name)
    for python_version in image.python_versions:
        image.push(python_version)


def push_to_registry(name: str, tags: List[str]) -> None:
    check.str_param(name, "name")
    check.list_param(tags, "tags", of_type=str)

    image = DagsterDockerImage(name)

    python_version = next(iter(image.python_versions))

    local_image = image.local_image(python_version)

    for tag in tags:
        execute_docker_tag(local_image, tag)
        execute_docker_push(tag)


@cli.command()
@opt_push_name
@opt_push_dagster_version
@opt_set_latest
def push_dockerhub(name: str, dagster_version: str, set_latest: bool):
    """Used for pushing k8s images to Docker Hub. Must be logged in to Docker Hub for this to
    succeed.
    """
    tags = [
        f"dagster/{name}:{dagster_version}",
    ]
    if set_latest:
        tags.append(f"dagster/{name}:latest")

    push_to_registry(name, tags)


@cli.command()
@opt_push_name
@opt_push_dagster_version
@opt_set_latest
def push_ecr(name: str, dagster_version: str, set_latest: bool):
    """Used for pushing k8s images to our public ECR.

    You must be authed for ECR. Run:

        aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/dagster
    """
    tags = [
        f"{AWS_ECR_REGISTRY}/{name}:{dagster_version}",
    ]
    if set_latest:
        tags.append(f"{AWS_ECR_REGISTRY}/{name}:latest")

    push_to_registry(name, tags)


def main():
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()


if __name__ == "__main__":
    main()
