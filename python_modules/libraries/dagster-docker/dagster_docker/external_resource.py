import os
import tempfile
from contextlib import ExitStack, contextmanager
from typing import Iterator, Mapping, Optional, Sequence, Tuple, Union

import docker
from dagster import OpExecutionContext
from dagster._core.external_execution.context import (
    ExternalExecutionOrchestrationContext,
)
from dagster._core.external_execution.resource import (
    ExternalExecutionContextInjector,
    ExternalExecutionMessageReader,
    ExternalExecutionResource,
)
from dagster._core.external_execution.utils import (
    get_file_context_injector,
    get_file_message_reader,
    io_params_as_env_vars,
)
from dagster_externals import (
    DagsterExternalsError,
    ExternalExecutionExtras,
)
from pydantic import Field
from typing_extensions import TypeAlias

VolumeMapping: TypeAlias = Mapping[str, Mapping[str, str]]


_CONTEXT_SOURCE_FILENAME = "context"
_MESSAGE_SINK_FILENAME = "messages"


class DockerExecutionResource(ExternalExecutionResource):
    env: Optional[Mapping[str, str]] = Field(
        default=None,
        description="An optional dict of environment variables to pass to the subprocess.",
    )
    volumes: Optional[VolumeMapping] = Field(
        default=None,
        description="An optional dict of volumes to mount in the container.",
    )
    registry: Optional[Mapping[str, str]] = Field(
        default=None,
        description="An optional dict of registry credentials to use to pull the image.",
    )

    def run(
        self,
        image: str,
        command: Union[str, Sequence[str]],
        *,
        context: OpExecutionContext,
        extras: Optional[ExternalExecutionExtras] = None,
        context_source: Optional[ExternalExecutionContextInjector] = None,
        message_sink: Optional[ExternalExecutionMessageReader] = None,
        env: Optional[Mapping[str, str]] = None,
        volumes: Optional[Mapping[str, Mapping[str, str]]] = None,
        registry: Optional[Mapping[str, str]] = None,
    ) -> None:
        external_context = ExternalExecutionOrchestrationContext(context=context, extras=extras)
        with self._setup_io(external_context, context_source, message_sink) as (io_env, io_volumes):
            client = docker.client.from_env()
            if registry:
                client.login(
                    registry=registry["url"],
                    username=registry["username"],
                    password=registry["password"],
                )

            # will need to deal with when its necessary to pull the image before starting the container
            # client.images.pull(image)

            container = client.containers.create(
                image=image,
                command=command,
                detach=True,
                environment={**self.get_base_env(), **(self.env or {}), **(env or {}), **io_env},
                volumes={
                    **(volumes or {}),
                    **io_volumes,
                },
            )

            result = container.start()
            try:
                for line in container.logs(stdout=True, stderr=True, stream=True, follow=True):
                    print(line)  # noqa: T201

                result = container.wait()
                if result["StatusCode"] != 0:
                    raise DagsterExternalsError(
                        f"Container exited with non-zero status code: {result}"
                    )
            finally:
                container.stop()

    @contextmanager
    def _setup_io(
        self,
        external_context: ExternalExecutionOrchestrationContext,
        context_injector: Optional[ExternalExecutionContextInjector],
        message_reader: Optional[ExternalExecutionMessageReader],
    ) -> Iterator[Tuple[Mapping[str, str], VolumeMapping]]:
        with ExitStack() as stack:
            if context_injector is None or message_reader is None:
                tempdir = stack.enter_context(tempfile.TemporaryDirectory())
                context_injector = context_injector or get_file_context_injector(
                    os.path.join(tempdir, _CONTEXT_SOURCE_FILENAME)
                )
                message_reader = message_reader or get_file_message_reader(
                    os.path.join(tempdir, _MESSAGE_SINK_FILENAME)
                )
                volumes = {tempdir: {"bind": tempdir, "mode": "rw"}}
            else:
                volumes = {}
            context_injector_params = stack.enter_context(context_injector(external_context))
            message_reader_params = stack.enter_context(message_reader(external_context))
            io_env = io_params_as_env_vars(context_injector_params, message_reader_params)
            yield io_env, volumes
