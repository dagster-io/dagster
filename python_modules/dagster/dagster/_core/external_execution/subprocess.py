import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from subprocess import Popen
from threading import Event, Thread
from typing import ContextManager, Iterator, Mapping, Optional, Sequence, Union

from dagster_external.protocol import (
    DAGSTER_EXTERNAL_ENV_KEYS,
    ExternalExecutionExtras,
    ExternalExecutionIOMode,
)
from pydantic import Field

import dagster._check as check
from dagster._core.errors import DagsterExternalExecutionError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.external_execution.resource import ExternalExecutionResource
from dagster._core.external_execution.task import (
    ExternalExecutionTask,
    ExternalTaskIOParams,
    ExternalTaskParams,
    SocketAddress,
)


@dataclass
class SubprocessTaskParams(ExternalTaskParams):
    command: Sequence[str]
    cwd: Optional[str] = None
    env: Mapping[str, str] = field(default_factory=dict)


@dataclass
class SubprocessTaskIOParams(ExternalTaskIOParams):
    stdio_fd: Optional[int] = None


class ExternalExecutionSubprocessTask(
    ExternalExecutionTask[SubprocessTaskParams, SubprocessTaskIOParams]
):
    def _launch(
        self,
        base_env: Mapping[str, str],
        params: SubprocessTaskParams,
        input_params: SubprocessTaskIOParams,
        output_params: SubprocessTaskIOParams,
    ) -> None:
        process = Popen(
            params.command,
            cwd=params.cwd,
            stdin=input_params.stdio_fd,
            stdout=output_params.stdio_fd,
            env={**base_env, **params.env, **input_params.env, **output_params.env},
        )
        process.wait()

        if process.returncode != 0:
            raise DagsterExternalExecutionError(
                f"External execution process failed with code {process.returncode}"
            )

    # ########################
    # ##### IO CONTEXT MANAGERS
    # ########################

    def _input_context_manager(
        self, tempdir: str, sockaddr: SocketAddress
    ) -> ContextManager[SubprocessTaskIOParams]:
        if self._input_mode == ExternalExecutionIOMode.stdio:
            return self._stdio_input()
        elif self._input_mode == ExternalExecutionIOMode.file:
            return self._file_input(tempdir)
        elif self._input_mode == ExternalExecutionIOMode.fifo:
            return self._fifo_input(tempdir)
        elif self._input_mode == ExternalExecutionIOMode.socket:
            assert sockaddr is not None, "`sockaddr` must be set when output_mode is `socket`"
            return self._socket_input(sockaddr)
        else:
            check.failed(f"Unsupported input mode: {self._input_mode}")

    @contextmanager
    def _stdio_input(self) -> Iterator[SubprocessTaskIOParams]:
        read_fd, write_fd = os.pipe()
        self._write_input(write_fd)
        yield SubprocessTaskIOParams(stdio_fd=read_fd)
        os.close(read_fd)

    @contextmanager
    def _file_input(self, tempdir: str) -> Iterator[SubprocessTaskIOParams]:
        path = self._prepare_io_path(self._input_path, "input", tempdir)
        env = {DAGSTER_EXTERNAL_ENV_KEYS["input"]: path}
        try:
            self._write_input(path)
            yield SubprocessTaskIOParams(env=env)
        finally:
            if os.path.exists(path):
                os.remove(path)

    @contextmanager
    def _fifo_input(self, tempdir: str) -> Iterator[SubprocessTaskIOParams]:
        path = self._prepare_io_path(self._input_path, "input", tempdir)
        if not os.path.exists(path):
            os.mkfifo(path)
        try:
            # Use thread to prevent blocking
            thread = Thread(target=self._write_input, args=(path,), daemon=True)
            thread.start()
            env = {DAGSTER_EXTERNAL_ENV_KEYS["input"]: path}
            yield SubprocessTaskIOParams(env=env)
            thread.join()
        finally:
            os.remove(path)

    # Socket server is started/shutdown in a dedicated context manager to share logic between input
    # and output.
    @contextmanager
    def _socket_input(self, sockaddr: SocketAddress) -> Iterator[SubprocessTaskIOParams]:
        env = {
            DAGSTER_EXTERNAL_ENV_KEYS["host"]: sockaddr[0],
            DAGSTER_EXTERNAL_ENV_KEYS["port"]: str(sockaddr[1]),
        }
        yield SubprocessTaskIOParams(env=env)

    def _output_context_manager(
        self, tempdir: str, sockaddr: Optional[SocketAddress]
    ) -> ContextManager[SubprocessTaskIOParams]:
        if self._output_mode == ExternalExecutionIOMode.stdio:
            return self._stdio_output()
        elif self._output_mode == ExternalExecutionIOMode.file:
            return self._file_output(tempdir)
        elif self._output_mode == ExternalExecutionIOMode.fifo:
            return self._fifo_output(tempdir)
        elif self._output_mode == ExternalExecutionIOMode.socket:
            assert sockaddr is not None, "`sockaddr` must be set when output_mode is `socket`"
            return self.socket_output(sockaddr)
        else:
            check.failed(f"Unsupported output mode: {self._output_mode}")

    @contextmanager
    def _stdio_output(self) -> Iterator[SubprocessTaskIOParams]:
        read_fd, write_fd = os.pipe()
        is_task_complete = Event()
        thread = None
        try:
            thread = self._start_output_thread(read_fd, is_task_complete)
            yield SubprocessTaskIOParams(stdio_fd=write_fd)
        finally:
            os.close(write_fd)
            is_task_complete.set()
            if thread:
                thread.join()

    @contextmanager
    def _file_output(self, tempdir: str) -> Iterator[SubprocessTaskIOParams]:
        path = self._prepare_io_path(self._output_path, "output", tempdir)
        env = {DAGSTER_EXTERNAL_ENV_KEYS["output"]: path}
        is_task_complete = Event()
        thread = None
        try:
            open(path, "w").close()  # create file
            thread = self._start_output_thread(path, is_task_complete)
            yield SubprocessTaskIOParams(env)
        finally:
            is_task_complete.set()
            if thread:
                thread.join()
            if os.path.exists(path):
                os.remove(path)

    @contextmanager
    def _fifo_output(self, tempdir: str) -> Iterator[SubprocessTaskIOParams]:
        path = self._prepare_io_path(self._output_path, "output", tempdir)
        env = {DAGSTER_EXTERNAL_ENV_KEYS["output"]: path}
        if not os.path.exists(path):
            os.mkfifo(path)
        is_task_complete = Event()
        thread = None
        dummy_handle = None
        try:
            thread = self._start_output_thread(path, is_task_complete)
            dummy_handle = os.open(path, os.O_RDWR | os.O_NONBLOCK)
            # We open a write file descriptor for a FIFO in the orchestration
            # process in order to keep the FIFO open for reading. Otherwise, the
            # FIFO will receive EOF after the first file descriptor writing it is
            # closed in an external process. Note that `O_RDWR` is required for
            # this call to succeed when no readers are yet available, and
            # `O_NONBLOCK` is required to prevent the `open` call from blocking.
            yield SubprocessTaskIOParams(env)
        finally:
            is_task_complete.set()
            if dummy_handle:
                os.close(dummy_handle)
            if thread:
                thread.join()
            if os.path.exists(path):
                os.remove(path)

    # Socket server is started/shutdown in a dedicated context manager to share logic between input
    # and output.
    @contextmanager
    def socket_output(self, sockaddr: SocketAddress) -> Iterator[SubprocessTaskIOParams]:
        env = {
            DAGSTER_EXTERNAL_ENV_KEYS["host"]: sockaddr[0],
            DAGSTER_EXTERNAL_ENV_KEYS["port"]: str(sockaddr[1]),
        }
        yield SubprocessTaskIOParams(env=env)

    # ########################
    # ##### IO ROUTINES
    # ########################

    def _start_output_thread(self, path_or_fd: Union[str, int], is_task_complete: Event) -> Thread:
        thread = Thread(target=self._read_output, args=(path_or_fd, is_task_complete), daemon=True)
        thread.start()
        return thread


class SubprocessExecutionResource(ExternalExecutionResource):
    cwd: Optional[str] = Field(
        default=None, description="Working directory in which to launch the subprocess command."
    )
    env: Optional[Mapping[str, str]] = Field(
        default=None,
        description="An optional dict of environment variables to pass to the subprocess.",
    )

    def run(
        self,
        command: Union[str, Sequence[str]],
        *,
        context: OpExecutionContext,
        extras: Optional[ExternalExecutionExtras] = None,
        env: Optional[Mapping[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> None:
        params = SubprocessTaskParams(
            command=command,
            env={**(env or {}), **(self.env or {})},
            cwd=(cwd or self.cwd),
        )
        ExternalExecutionSubprocessTask(
            context=context,
            extras=extras,
            input_mode=self.input_mode,
            output_mode=self.output_mode,
            input_path=self.input_path,
            output_path=self.output_path,
        ).run(params)
