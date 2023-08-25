import os
import tempfile
from contextlib import contextmanager
from typing import Iterator, Mapping, Optional, Sequence, Tuple, Union

import docker
from dagster import OpExecutionContext
from dagster._core.external_execution.resource import (
    ExternalExecutionResource,
)
from dagster._core.external_execution.task import (
    ExternalExecutionTask,
)
from dagster._core.external_execution.utils import (
    file_context_source,
    file_message_sink,
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


class DockerExecutionTask(ExternalExecutionTask):
    def run(
        self,
        image: str,
        command: Union[str, Sequence[str]],
        registry: Optional[Mapping[str, str]] = None,
        volumes: Optional[Mapping[str, Mapping[str, str]]] = None,
        ports: Optional[Mapping[str, Mapping[int, int]]] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> None:
        with self._setup_io() as (io_env, io_volumes):
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
                environment={**self.get_base_env(), **(env or {}), **io_env},
                volumes={
                    **(volumes or {}),
                    **io_volumes,
                },
                ports=ports,
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

    # ########################
    # ##### IO
    # ########################

    @contextmanager
    def _setup_io(self) -> Iterator[Tuple[Mapping[str, str], VolumeMapping]]:
        with tempfile.TemporaryDirectory() as tempdir, file_context_source(
            self, os.path.join(tempdir, _CONTEXT_SOURCE_FILENAME)
        ) as context_env, file_message_sink(
            self, os.path.join(tempdir, _MESSAGE_SINK_FILENAME)
        ) as message_env:
            volumes = {tempdir: {"bind": tempdir, "mode": "rw"}}
            yield {**context_env, **message_env}, volumes


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
        extras: ExternalExecutionExtras,
        env: Optional[Mapping[str, str]] = None,
        volumes: Optional[Mapping[str, Mapping[str, str]]] = None,
        registry: Optional[Mapping[str, str]] = None,
    ) -> None:
        DockerExecutionTask(
            context=context,
            extras=extras,
        ).run(
            image=image,
            command=command,
            registry=registry or self.registry,
            volumes={**(volumes or {}), **(self.volumes or {})},
            env={**(env or {}), **(self.env or {})},
        )
