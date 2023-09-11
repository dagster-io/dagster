from contextlib import contextmanager
from typing import Any, Iterator, Mapping, Optional, Sequence, Union

import docker
from dagster import (
    OpExecutionContext,
    ResourceParam,
    _check as check,
)
from dagster._core.ext.client import (
    ExtClient,
    ExtContextInjector,
    ExtMessageReader,
)
from dagster._core.ext.context import (
    ExtMessageHandler,
)
from dagster._core.ext.utils import (
    ExtEnvContextInjector,
    ext_protocol,
    extract_message_or_forward_to_stdout,
)
from dagster_ext import (
    DagsterExtError,
    ExtDefaultMessageWriter,
    ExtExtras,
    ExtParams,
)


class DockerLogsMessageReader(ExtMessageReader):
    @contextmanager
    def read_messages(
        self,
        handler: ExtMessageHandler,
    ) -> Iterator[ExtParams]:
        self._handler = handler
        try:
            yield {ExtDefaultMessageWriter.STDIO_KEY: ExtDefaultMessageWriter.STDERR}
        finally:
            self._handler = None

    def consume_docker_logs(self, container):
        handler = check.not_none(
            self._handler, "Can only consume logs within context manager scope."
        )
        for log_line in container.logs(stdout=True, stderr=True, stream=True, follow=True):
            extract_message_or_forward_to_stdout(handler, log_line)


class _ExtDocker(ExtClient):
    """An ext protocol compliant resource for launching docker containers.

    By default context is injected via environment variables and messages are parsed out of the
    log stream and other logs are forwarded to stdout of the orchestration process.

    Args:
        env (Optional[Mapping[str, str]]): An optional dict of environment variables to pass to the subprocess.
        register (Optional[Mapping[str, str]]): An optional dict of registry credentials to login the docker client.
    """

    def __init__(
        self, env: Optional[Mapping[str, str]] = None, registry: Optional[Mapping[str, str]] = None
    ):
        self.env = check.opt_mapping_param(env, "env", key_type=str, value_type=str)
        self.registry = check.opt_mapping_param(registry, "registry", key_type=str, value_type=str)

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
        context_injector = context_injector or ExtEnvContextInjector()
        message_reader = message_reader or DockerLogsMessageReader()

        with ext_protocol(
            context=context,
            context_injector=context_injector,
            message_reader=message_reader,
            extras=extras,
        ) as ext_context:
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
                    ext_protocol_env=ext_context.get_external_process_env_vars(),
                    container_kwargs=container_kwargs,
                )
            except docker.errors.ImageNotFound:
                client.images.pull(image)
                container = self._create_container(
                    client=client,
                    image=image,
                    command=command,
                    env=env,
                    ext_protocol_env=ext_context.get_external_process_env_vars(),
                    container_kwargs=container_kwargs,
                )

            result = container.start()
            try:
                if isinstance(message_reader, DockerLogsMessageReader):
                    message_reader.consume_docker_logs(container)

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
        ext_protocol_env: Mapping[str, str],
    ):
        kwargs = dict(container_kwargs or {})
        kwargs_env = kwargs.pop("environment", {})
        return client.containers.create(
            image=image,
            command=command,
            detach=True,
            environment={
                **ext_protocol_env,
                **(self.env or {}),
                **(env or {}),
                **kwargs_env,
            },
            **kwargs,
        )


ExtDocker = ResourceParam[_ExtDocker]
