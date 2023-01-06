from dagster import (
    Field,
    StringSource,
    _check as check,
)
from dagster._utils.merger import merge_dicts
from docker_image import reference

from .container_context import DOCKER_CONTAINER_CONTEXT_SCHEMA

DOCKER_CONFIG_SCHEMA = merge_dicts(
    {
        "image": Field(
            StringSource,
            is_required=False,
            description="The docker image to be used if the repository does not specify one.",
        ),
        "network": Field(
            StringSource,
            is_required=False,
            description=(
                "Name of the network to which to connect the launched container at creation time"
            ),
        ),
    },
    DOCKER_CONTAINER_CONTEXT_SCHEMA,
)


def validate_docker_config(network, networks, container_kwargs):
    if network:
        check.invariant(not networks, "cannot set both `network` and `networks`")

    if container_kwargs:
        if "image" in container_kwargs:
            raise Exception(
                "'image' cannot be used in 'container_kwargs'. Use the 'image' config key instead."
            )

        if "environment" in container_kwargs:
            raise Exception(
                "'environment' cannot be used in 'container_kwargs'. Use the 'env_vars' config key"
                " instead."
            )

        if "network" in container_kwargs:
            raise Exception(
                "'network' cannot be used in 'container_kwargs'. Use the 'networks' config key"
                " instead."
            )


def validate_docker_image(docker_image):
    try:
        # validate that the docker image name is valid
        reference.Reference.parse(docker_image)
    except Exception as e:
        raise Exception(
            "Docker image name {docker_image} is not correctly formatted".format(
                docker_image=docker_image
            )
        ) from e
