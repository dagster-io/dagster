from typing import List

import click
from dagster import check

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
        print(image.image)  # pylint: disable=print-call


@cli.command()
@click.option("--name", required=True, help="Name of image to build")
@click.option(
    "--dagster-version", required=True, help="Version of image to build",
)
@click.option(
    "-t",
    "--timestamp",
    type=click.STRING,
    required=False,
    default=current_time_str(),
    help="Timestamp to build in format 2020-07-11T040642 (defaults to now UTC)",
)
@click.option("-v", "--python-version", type=click.STRING, required=True)
def build(name, dagster_version, timestamp, python_version):
    get_image(name).build(timestamp, dagster_version, python_version)


@cli.command()
@click.option("--name", required=True, help="Name of image to build")
@click.option(
    "--dagster-version",
    required=True,
    help="Version of image to build, must match current dagster version",
)
@click.option(
    "-t",
    "--timestamp",
    type=click.STRING,
    required=False,
    default=current_time_str(),
    help="Timestamp to build in format 2020-07-11T040642 (defaults to now UTC)",
)
def build_all(name, dagster_version, timestamp):
    """Build all supported python versions for image"""
    image = get_image(name)

    for python_version in image.python_versions:
        image.build(timestamp, dagster_version, python_version)


@cli.command()
@click.option("--name", required=True, help="Name of image to push")
@click.option("-v", "--python-version", type=click.STRING, required=True)
@click.option("-v", "--custom-tag", type=click.STRING, required=False)
def push(name, python_version, custom_tag):
    ensure_ecr_login()
    get_image(name).push(python_version, custom_tag=custom_tag)


@cli.command()
@click.option("--name", required=True, help="Name of image to push")
def push_all(name):
    ensure_ecr_login()
    image = get_image(name)
    for python_version in image.python_versions:
        image.push(python_version)


def push_to_registry(name: str, tags: List[str]):
    check.str_param(name, "name")
    check.list_param(tags, "tags", of_type=str)

    image = DagsterDockerImage(name)

    python_version = next(iter(image.python_versions))

    local_image = image.local_image(python_version)

    for tag in tags:
        execute_docker_tag(local_image, tag)
        execute_docker_push(tag)


@cli.command()
@click.option("--name", required=True, help="Name of image to push")
@click.option(
    "--dagster-version", required=True, help="Version of image to push",
)
def push_dockerhub(name, dagster_version):
    """Used for pushing k8s images to Docker Hub. Must be logged in to Docker Hub for this to
    succeed.
    """

    tags = [f"dagster/{name}:{dagster_version}", f"dagster/{name}:latest"]

    push_to_registry(name, tags)


@cli.command()
@click.option("--name", required=True, help="Name of image to push")
@click.option(
    "--dagster-version", required=True, help="Version of image to push",
)
def push_ecr(name, dagster_version):
    """Used for pushing k8s images to our public ECR.

    You must be authed for ECR. Run:

        aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/dagster
    """

    tags = [
        f"{AWS_ECR_REGISTRY}/{name}:{dagster_version}",
        f"{AWS_ECR_REGISTRY}/{name}:latest",
    ]

    push_to_registry(name, tags)


def main():
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()


if __name__ == "__main__":
    main()
