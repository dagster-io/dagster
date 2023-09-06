from contextlib import contextmanager
from typing import Any, Iterator, Mapping, Optional, Sequence, Tuple, Union

import docker
from dagster import OpExecutionContext
from dagster._core.ext.context import (
    ExtOrchestrationContext,
)
from dagster._core.ext.resource import (
    ExtContextInjector,
    ExtMessageReader,
    ExtResource,
)
from dagster._core.ext.utils import (
    ExtEnvContextInjector,
    extract_message_or_forward_to_stdout,
    io_params_as_env_vars,
)
from dagster_ext import (
    DagsterExtError,
    ExtDefaultMessageWriter,
    ExtExtras,
    ExtParams,
)
from pydantic import Field


class DockerLogsMessageReader(ExtMessageReader):
    @contextmanager
    def read_messages(
        self,
        _context: ExtOrchestrationContext,
    ) -> Iterator[ExtParams]:
        yield {ExtDefaultMessageWriter.STDIO_KEY: ExtDefaultMessageWriter.STDERR}

    def consume_docker_logs(self, container, ext_context):
        for log_line in container.logs(stdout=True, stderr=True, stream=True, follow=True):
            extract_message_or_forward_to_stdout(ext_context, log_line)


class ExtDocker(ExtResource):
    """An ext protocol compliant resource for launching docker containers.

    By default context is injected via environment variables and messages are parsed out of the
    log stream and other logs are forwarded to stdout of the orchestration process.
    """

    env: Optional[Mapping[str, str]] = Field(
        default=None,
        description="An optional dict of environment variables to set on the container.",
    )

    registry: Optional[Mapping[str, str]] = Field(
        default=None,
        description="An optional dict of registry credentials to use to login the docker client.",
    )

    def run(
        self,
        *,
        context: OpExecutionContext,
        image: str,
        command: Union[str, Sequence[str]],
        env: Optional[Mapping[str, str]] = None,
        registry: Optional[Mapping[str, str]] = None,
        container_kwargs: Optional[Mapping[str, Any]] = None,
        extras: Optional[ExtExtras] = None,
        context_injector: Optional[ExtContextInjector] = None,
        message_reader: Optional[ExtMessageReader] = None,
    ) -> None:
        """Create a docker container and run it to completion, enriched with the ext protocol.

        Args:
            image (str):
                The image for the container to use.
            command (Optional[Union[str, Sequence[str]]]):
                The command for the container use.
            env (Optional[Mapping[str,str]]):
                A mapping of environment variable names to values to set on the first
                container in the pod spec, on top of those configured on resource.
            registry (Optional[Mapping[str, str]]:
                A mapping containing url, username, and password to be used
                with docker client login.
            container_kwargs (Optional[Mapping[str, Any]]:
                Arguments to be forwarded to docker client containers.create.
            extras (Optional[ExtExtras]):
                Extra values to pass along as part of the ext protocol.
            context_injector (Optional[ExtContextInjector]):
                Override the default ext protocol context injection.
            message_Reader (Optional[ExtMessageReader]):
                Override the default ext protocol message reader.
        """
        ext_context = ExtOrchestrationContext(context=context, extras=extras)
        with self._setup_ext_protocol(ext_context, context_injector, message_reader) as (
            ext_env,
            message_reader,
        ):
            client = docker.client.from_env()
            registry = registry or self.registry
            if registry:
                client.login(
                    registry=registry["url"],
                    username=registry["username"],
                    password=registry["password"],
                )

            try:
                container = self._create_container(
                    client=client,
                    image=image,
                    command=command,
                    env=env,
                    ext_env=ext_env,
                    container_kwargs=container_kwargs,
                )
            except docker.errors.ImageNotFound:
                client.images.pull(image)
                container = self._create_container(
                    client=client,
                    image=image,
                    command=command,
                    env=env,
                    ext_env=ext_env,
                    container_kwargs=container_kwargs,
                )

            result = container.start()
            try:
                if isinstance(message_reader, DockerLogsMessageReader):
                    message_reader.consume_docker_logs(container, ext_context)

                result = container.wait()
                if result["StatusCode"] != 0:
                    raise DagsterExtError(f"Container exited with non-zero status code: {result}")
            finally:
                container.stop()

    def _create_container(
        self,
        client,
        image: str,
        command: Union[str, Sequence[str]],
        env: Optional[Mapping[str, str]],
        container_kwargs: Optional[Mapping[str, Any]],
        ext_env: Mapping[str, str],
    ):
        kwargs = dict(container_kwargs or {})
        kwargs_env = kwargs.pop("environment", {})
        return client.containers.create(
            image=image,
            command=command,
            detach=True,
            environment={
                **self.get_base_env(),
                **ext_env,
                **(self.env or {}),
                **(env or {}),
                **kwargs_env,
            },
            **kwargs,
        )

    @contextmanager
    def _setup_ext_protocol(
        self,
        external_context: ExtOrchestrationContext,
        context_injector: Optional[ExtContextInjector],
        message_reader: Optional[ExtMessageReader],
    ) -> Iterator[Tuple[Mapping[str, str], ExtMessageReader]]:
        context_injector = context_injector or ExtEnvContextInjector()
        message_reader = message_reader or DockerLogsMessageReader()

        with context_injector.inject_context(
            external_context,
        ) as ci_params, message_reader.read_messages(
            external_context,
        ) as mr_params:
            protocol_envs = io_params_as_env_vars(ci_params, mr_params)
            yield protocol_envs, message_reader
