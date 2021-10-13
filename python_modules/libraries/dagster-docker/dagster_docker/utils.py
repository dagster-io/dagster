from dagster import Array, Field, Permissive, StringSource, check
from docker_image import reference

DOCKER_CONFIG_SCHEMA = {
    "image": Field(
        StringSource,
        is_required=False,
        description="The docker image to be used if the repository does not specify one.",
    ),
    "registry": Field(
        {
            "url": Field(StringSource),
            "username": Field(StringSource),
            "password": Field(StringSource),
        },
        is_required=False,
        description="Information for using a non local/public docker registry",
    ),
    "env_vars": Field(
        [str],
        is_required=False,
        description="The list of environment variables names to forward to the docker container",
    ),
    "network": Field(
        StringSource,
        is_required=False,
        description="Name of the network to which to connect the launched container at creation time",
    ),
    "networks": Field(
        Array(StringSource),
        is_required=False,
        description="Names of the networks to which to connect the launched container at creation time",
    ),
    "container_kwargs": Field(
        Permissive(),
        is_required=False,
        description="key-value pairs that can be passed into containers.create. See "
        "https://docker-py.readthedocs.io/en/stable/containers.html for the full list "
        "of available options.",
    ),
}


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
                "'environment' cannot be used in 'container_kwargs'. Use the 'environment' config key instead."
            )

        if "network" in container_kwargs:
            raise Exception(
                "'network' cannot be used in 'container_kwargs'. Use the 'network' config key instead."
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
