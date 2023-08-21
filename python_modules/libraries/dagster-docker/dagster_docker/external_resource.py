import os
import tempfile
from contextlib import ExitStack
from typing import Mapping, Optional, Sequence, Union

import docker
from dagster import OpExecutionContext
from dagster._core.external_execution.resource import (
    SubprocessExecutionResource,
)
from dagster._core.external_execution.task import ExternalExecutionTask
from dagster_external.protocol import (
    DAGSTER_EXTERNAL_ENV_KEYS,
    ExternalExecutionExtras,
    ExternalExecutionIOMode,
)


class DockerExecutionTask(ExternalExecutionTask):
    def run(
        self,
        image: str,
        volumes: Optional[Mapping[str, Mapping[str, str]]] = None,
        registry=None,
    ) -> None:
        base_env = {
            **os.environ,
            **self.env,
            DAGSTER_EXTERNAL_ENV_KEYS["input_mode"]: self._input_mode.value,
            DAGSTER_EXTERNAL_ENV_KEYS["output_mode"]: self._output_mode.value,
        }

        with ExitStack() as stack:
            # this tempdir dependency should be more explicit - passed in to dependent entities
            self._tempdir = stack.enter_context(tempfile.TemporaryDirectory())
            stdin_fd, input_env_vars = stack.enter_context(self._input_context_manager())
            stdout_fd, output_env_vars = stack.enter_context(self._output_context_manager())

            # assert in a compatible mode (more checks likely required)
            assert stdin_fd is None and stdout_fd is None

            # file IPC - need an easy way to have path not be the same on both sides
            ipc_volume_mounts = {}
            if self._input_mode == ExternalExecutionIOMode.file:
                # not great to have to fish this out of env vars
                input_file_path = input_env_vars[DAGSTER_EXTERNAL_ENV_KEYS["input"]]
                input_file_dir = os.path.dirname(input_file_path)
                ipc_volume_mounts[input_file_dir] = {
                    "bind": input_file_dir,
                    "mode": "rw",
                }
            if self._output_mode == ExternalExecutionIOMode.file:
                output_file_path = output_env_vars[DAGSTER_EXTERNAL_ENV_KEYS["output"]]
                output_file_dir = os.path.dirname(output_file_path)
                ipc_volume_mounts[output_file_dir] = {
                    "bind": output_file_dir,
                    "mode": "rw",
                }

            # socket IPC - have to override to handle asymmetry
            ipc_ports = {}
            env_overrides = {}
            if ExternalExecutionIOMode.socket in (self._input_mode, self._output_mode):
                _host, port = stack.enter_context(self._socket_server_context_manager())
                ipc_ports = {port: port}
                # assumes previous value was "localhost", not overriding input/output env vars directly since Mappings
                env_overrides[DAGSTER_EXTERNAL_ENV_KEYS["host"]] = "host.docker.internal"

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
                command=self._command,
                detach=True,
                environment={
                    **base_env,
                    **input_env_vars,
                    **output_env_vars,
                    **env_overrides,
                },
                volumes={
                    **ipc_volume_mounts,
                    **(volumes or {}),
                    # other volumes...
                },
                ports={
                    **ipc_ports,
                    # other ports...
                },
            )

            result = container.start()
            try:
                for line in container.logs(stdout=True, stderr=True, stream=True, follow=True):
                    # log mirroring
                    print(line)  # noqa: T201

                result = container.wait()
                return result["StatusCode"]
            finally:
                container.stop()


class DockerExecutionResource(SubprocessExecutionResource):
    def run(
        self,
        image: str,
        command: Union[str, Sequence[str]],
        context: OpExecutionContext,
        extras: ExternalExecutionExtras,
        env: Optional[Mapping[str, str]] = None,
        volumes: Optional[Mapping[str, Mapping[str, str]]] = None,
        registry=None,
    ) -> None:
        DockerExecutionTask(
            command=command,
            context=context,
            extras=extras,
            env={**(self.env or {}), **(env or {})},
            input_mode=self.input_mode,
            output_mode=self.output_mode,
            input_path=self.input_path,
            output_path=self.output_path,
        ).run(  # passing here since overriding Task __init__ seems rough
            image,
            volumes,
            registry,
        )
