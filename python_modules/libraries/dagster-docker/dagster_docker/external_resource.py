import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Event
from typing import ContextManager, Iterator, Mapping, Optional, Sequence, Union

import docker
from dagster import OpExecutionContext
from dagster._core.external_execution.resource import (
    ExternalExecutionResource,
)
from dagster._core.external_execution.task import (
    ExternalExecutionTask,
    ExternalTaskIOParams,
    ExternalTaskParams,
    SocketAddress,
)
from dagster_external.protocol import (
    DAGSTER_EXTERNAL_ENV_KEYS,
    ExternalExecutionExtras,
)
from dagster_external.util import DagsterExternalError


@dataclass
class DockerTaskParams(ExternalTaskParams):
    image: str
    command: Union[str, Sequence[str]]
    registry: Optional[Mapping[str, str]] = None
    volumes: Mapping[str, Mapping[str, str]] = field(default_factory=dict)
    env: Mapping[str, str] = field(default_factory=dict)


@dataclass
class DockerTaskIOParams(ExternalTaskIOParams):
    ports: Mapping[int, int] = field(default_factory=dict)
    volumes: Mapping[str, Mapping[str, str]] = field(default_factory=dict)


class DockerExecutionTask(ExternalExecutionTask[DockerTaskParams, DockerTaskIOParams]):
    def _launch(
        self,
        base_env: Mapping[str, str],
        params: DockerTaskParams,
        input_params: DockerTaskIOParams,
        output_params: DockerTaskIOParams,
    ) -> None:
        client = docker.client.from_env()
        if params.registry:
            client.login(
                registry=params.registry["url"],
                username=params.registry["username"],
                password=params.registry["password"],
            )

        # will need to deal with when its necessary to pull the image before starting the container
        # client.images.pull(image)

        container = client.containers.create(
            image=params.image,
            command=params.command,
            detach=True,
            environment={**base_env, **params.env, **input_params.env, **output_params.env},
            volumes={
                **params.volumes,
                **input_params.volumes,
                **output_params.volumes,
            },
            ports={
                **input_params.ports,
                **output_params.ports,
            },
        )

        result = container.start()
        try:
            for line in container.logs(stdout=True, stderr=True, stream=True, follow=True):
                print(line)  # noqa: T201

            result = container.wait()
            if result["StatusCode"] != 0:
                raise DagsterExternalError(f"Container exited with non-zero status code: {result}")
        finally:
            container.stop()

    # ########################
    # ##### IO CONTEXT MANAGERS
    # ########################

    def _input_context_manager(
        self, tempdir: str, sockaddr: SocketAddress
    ) -> ContextManager[DockerTaskIOParams]:
        return self._file_input(tempdir)

    @contextmanager
    def _file_input(self, tempdir: str) -> Iterator[DockerTaskIOParams]:
        path = self._prepare_io_path(self._input_path, "input", tempdir)
        env = {DAGSTER_EXTERNAL_ENV_KEYS["input"]: path}
        try:
            self._write_input(path)
            path_dir = os.path.dirname(path)
            volumes = {path_dir: {"bind": path_dir, "mode": "rw"}}
            yield DockerTaskIOParams(env=env, volumes=volumes)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def _output_context_manager(
        self, tempdir: str, params: DockerTaskParams
    ) -> ContextManager[DockerTaskIOParams]:
        return self._file_output(tempdir)

    @contextmanager
    def _file_output(self, tempdir: str) -> Iterator[DockerTaskIOParams]:
        path = self._prepare_io_path(self._output_path, "output", tempdir)
        env = {DAGSTER_EXTERNAL_ENV_KEYS["output"]: path}
        output_file_dir = os.path.dirname(path)
        volume_mounts = {output_file_dir: {"bind": output_file_dir, "mode": "rw"}}
        is_task_complete = Event()
        thread = None
        try:
            open(path, "w").close()  # create file
            thread = self._start_output_thread(path, is_task_complete)
            yield DockerTaskIOParams(env=env, volumes=volume_mounts)
        finally:
            is_task_complete.set()
            if thread:
                thread.join()
            if os.path.exists(path):
                os.remove(path)


class DockerExecutionResource(ExternalExecutionResource):
    def run(
        self,
        context: OpExecutionContext,
        image: str,
        command: Union[str, Sequence[str]],
        *,
        extras: ExternalExecutionExtras,
        env: Optional[Mapping[str, str]] = None,
        volumes: Optional[Mapping[str, Mapping[str, str]]] = None,
        registry: Optional[Mapping[str, str]] = None,
    ) -> None:
        params = DockerTaskParams(
            image=image,
            command=command,
            registry=registry,
            volumes=volumes or {},
            env=env or {},
        )

        DockerExecutionTask(
            context=context,
            extras=extras,
            input_path=self.input_path,
            output_path=self.output_path,
        ).run(params)
