from collections.abc import Mapping, Sequence
from typing import Any, Optional

import docker
import docker.errors
from dagster import Field, In, Nothing, OpExecutionContext, StringSource, op
from dagster._annotations import beta
from dagster._core.utils import parse_env_var
from dagster_shared.serdes.utils import hash_str

from dagster_docker.container_context import DockerContainerContext
from dagster_docker.docker_run_launcher import DockerRunLauncher
from dagster_docker.utils import DOCKER_CONFIG_SCHEMA, validate_docker_image

DOCKER_CONTAINER_OP_CONFIG = {
    **DOCKER_CONFIG_SCHEMA,
    "image": Field(
        StringSource,
        is_required=True,
        description="The image in which to run the Docker container.",
    ),
    "entrypoint": Field(
        [str],
        is_required=False,
        description="The ENTRYPOINT for the Docker container",
    ),
    "command": Field(
        [str],
        is_required=False,
        description="The command to run in the container within the launched Docker container.",
    ),
}


def _get_client(docker_container_context: DockerContainerContext):
    client = docker.client.from_env()
    if docker_container_context.registry:
        client.login(
            registry=docker_container_context.registry["url"],
            username=docker_container_context.registry["username"],
            password=docker_container_context.registry["password"],
        )
    return client


def _get_container_name(run_id, op_name, retry_number):
    container_name = hash_str(run_id + op_name)

    if retry_number > 0:
        container_name = f"{container_name}-{retry_number}"

    return container_name


def _create_container(
    op_context: OpExecutionContext,
    client,
    container_context: DockerContainerContext,
    image: str,
    entrypoint: Optional[Sequence[str]],
    command: Optional[Sequence[str]],
):
    env_vars = dict([parse_env_var(env_var) for env_var in container_context.env_vars])
    return client.containers.create(
        image,
        name=_get_container_name(op_context.run_id, op_context.op.name, op_context.retry_number),
        detach=True,
        network=container_context.networks[0] if len(container_context.networks) else None,
        entrypoint=entrypoint,
        command=command,
        environment=env_vars,
        **container_context.container_kwargs,
    )


@beta
def execute_docker_container(
    context: OpExecutionContext,
    image: str,
    entrypoint: Optional[Sequence[str]] = None,
    command: Optional[Sequence[str]] = None,
    networks: Optional[Sequence[str]] = None,
    registry: Optional[Mapping[str, str]] = None,
    env_vars: Optional[Sequence[str]] = None,
    container_kwargs: Optional[Mapping[str, Any]] = None,
):
    """This function is a utility for executing a Docker container from within a Dagster op.

    Args:
        image (str): The image to use for the launched Docker container.
        entrypoint (Optional[Sequence[str]]): The ENTRYPOINT to run in the launched Docker
            container. Default: None.
        command (Optional[Sequence[str]]): The CMD to run in the launched Docker container.
            Default: None.
        networks (Optional[Sequence[str]]): Names of the Docker networks to which to connect the
            launched container. Default: None.
        registry: (Optional[Mapping[str, str]]): Information for using a non local/public Docker
            registry. Can have "url", "username", or "password" keys.
        env_vars (Optional[Sequence[str]]): List of environemnt variables to include in the launched
            container. ach can be of the form KEY=VALUE or just KEY (in which case the value will be
            pulled from the calling environment.
        container_kwargs (Optional[Dict[str[Any]]]): key-value pairs that can be passed into
            containers.create in the Docker Python API. See
            https://docker-py.readthedocs.io/en/stable/containers.html for the full list
            of available options.
    """
    run_container_context = DockerContainerContext.create_for_run(
        context.dagster_run,
        (
            context.instance.run_launcher
            if isinstance(context.instance.run_launcher, DockerRunLauncher)
            else None
        ),
    )

    validate_docker_image(image)

    op_container_context = DockerContainerContext(
        registry=registry, env_vars=env_vars, networks=networks, container_kwargs=container_kwargs
    )

    container_context = run_container_context.merge(op_container_context)

    client = _get_client(container_context)

    try:
        container = _create_container(
            context, client, container_context, image, entrypoint, command
        )
    except docker.errors.ImageNotFound:
        client.images.pull(image)
        container = _create_container(
            context, client, container_context, image, entrypoint, command
        )

    if len(container_context.networks) > 1:
        for network_name in container_context.networks[1:]:
            network = client.networks.get(network_name)
            network.connect(container)

    container.start()

    for line in container.logs(stdout=True, stderr=True, stream=True, follow=True):
        print(line)  # noqa: T201

    exit_status = container.wait()["StatusCode"]

    if exit_status != 0:
        raise Exception(f"Docker container returned exit code {exit_status}")


@op(ins={"start_after": In(Nothing)}, config_schema=DOCKER_CONTAINER_OP_CONFIG)
@beta
def docker_container_op(context):
    """An op that runs a Docker container using the docker Python API.

    Contrast with the `docker_executor`, which runs each Dagster op in a Dagster job in its
    own Docker container.

    This op may be useful when:
      - You need to orchestrate a command that isn't a Dagster op (or isn't written in Python)
      - You want to run the rest of a Dagster job using a specific executor, and only a single
        op in docker.

    For example:

    .. literalinclude:: ../../../../../../python_modules/libraries/dagster-docker/dagster_docker_tests/test_example_docker_container_op.py
      :start-after: start_marker
      :end-before: end_marker
      :language: python

    You can create your own op with the same implementation by calling the `execute_docker_container` function
    inside your own op.
    """
    execute_docker_container(context, **context.op_config)
