from contextlib import contextmanager
from typing import Any, Iterator, Mapping, Optional, Sequence, Union

import docker
from dagster import (
    OpExecutionContext,
    ResourceParam,
    _check as check,
)
from dagster._annotations import experimental
from dagster._core.pipes.client import (
    PipesClient,
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.context import (
    PipesMessageHandler,
)
from dagster._core.pipes.utils import (
    PipesEnvContextInjector,
    extract_message_or_forward_to_stdout,
    open_pipes_session,
)
from dagster_pipes import (
    DagsterPipesError,
    PipesDefaultMessageWriter,
    PipesExtras,
    PipesParams,
)


@experimental
class PipesDockerLogsMessageReader(PipesMessageReader):
    @contextmanager
    def read_messages(
        self,
        handler: PipesMessageHandler,
    ) -> Iterator[PipesParams]:
        self._handler = handler
        try:
            yield {PipesDefaultMessageWriter.STDIO_KEY: PipesDefaultMessageWriter.STDERR}
        finally:
            self._handler = None

    def consume_docker_logs(self, container) -> None:
        handler = check.not_none(
            self._handler, "Can only consume logs within context manager scope."
        )
        for log_line in container.logs(stdout=True, stderr=True, stream=True, follow=True):
            extract_message_or_forward_to_stdout(handler, log_line)


@experimental
class _PipesDockerClient(PipesClient):
    """A pipes client that runs external processes in docker containers.

    By default context is injected via environment variables and messages are parsed out of the
    log stream, with other logs forwarded to stdout of the orchestration process.

    Args:
        env (Optional[Mapping[str, str]]): An optional dict of environment variables to pass to the
            container.
        register (Optional[Mapping[str, str]]): An optional dict of registry credentials to login to
            the docker client.
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into the docker container process. Defaults to :py:class:`PipesEnvContextInjector`.
        message_reader (Optional[PipesContextInjector]): A message reader to use to read messages
            from the docker container process. Defaults to :py:class:`DockerLogsMessageReader`.
    """

    def __init__(
        self,
        env: Optional[Mapping[str, str]] = None,
        registry: Optional[Mapping[str, str]] = None,
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[PipesMessageReader] = None,
    ):
        self.env = check.opt_mapping_param(env, "env", key_type=str, value_type=str)
        self.registry = check.opt_mapping_param(registry, "registry", key_type=str, value_type=str)
        self.context_injector = (
            check.opt_inst_param(
                context_injector,
                "context_injector",
                PipesContextInjector,
            )
            or PipesEnvContextInjector()
        )

        self.message_reader = (
            check.opt_inst_param(message_reader, "message_reader", PipesMessageReader)
            or PipesDockerLogsMessageReader()
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
        extras: Optional[PipesExtras] = None,
    ) -> PipesClientCompletedInvocation:
        """Create a docker container and run it to completion, enriched with the pipes protocol.

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
            extras (Optional[PipesExtras]):
                Extra values to pass along as part of the ext protocol.
            context_injector (Optional[PipesContextInjector]):
                Override the default ext protocol context injection.
            message_reader (Optional[PipesMessageReader]):
                Override the default ext protocol message reader.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
                process.
        """
        with open_pipes_session(
            context=context,
            context_injector=self.context_injector,
            message_reader=self.message_reader,
            extras=extras,
        ) as pipes_session:
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
                    open_pipes_session_env=pipes_session.get_bootstrap_env_vars(),
                    container_kwargs=container_kwargs,
                )
            except docker.errors.ImageNotFound:
                client.images.pull(image)
                container = self._create_container(
                    client=client,
                    image=image,
                    command=command,
                    env=env,
                    open_pipes_session_env=pipes_session.get_bootstrap_env_vars(),
                    container_kwargs=container_kwargs,
                )

            result = container.start()
            try:
                if isinstance(self.message_reader, PipesDockerLogsMessageReader):
                    self.message_reader.consume_docker_logs(container)

                result = container.wait()
                if result["StatusCode"] != 0:
                    raise DagsterPipesError(f"Container exited with non-zero status code: {result}")
            finally:
                container.stop()
        return PipesClientCompletedInvocation(tuple(pipes_session.get_results()))

    def _create_container(
        self,
        client,
        image: str,
        command: Union[str, Sequence[str]],
        env: Optional[Mapping[str, str]],
        container_kwargs: Optional[Mapping[str, Any]],
        open_pipes_session_env: Mapping[str, str],
    ):
        kwargs = dict(container_kwargs or {})
        kwargs_env = kwargs.pop("environment", {})
        return client.containers.create(
            image=image,
            command=command,
            detach=True,
            environment={
                **open_pipes_session_env,
                **(self.env or {}),
                **(env or {}),
                **kwargs_env,
            },
            **kwargs,
        )


PipesDockerClient = ResourceParam[_PipesDockerClient]
