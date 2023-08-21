import json
import os
import socket
import socketserver
import tempfile
import time
from contextlib import ExitStack, contextmanager
from copy import copy
from subprocess import Popen
from threading import Event, Thread
from typing import Any, ContextManager, Iterator, Mapping, Optional, Sequence, Tuple, Union

from dagster_external.protocol import (
    DAGSTER_EXTERNAL_DEFAULT_HOST,
    DAGSTER_EXTERNAL_DEFAULT_INPUT_FILENAME,
    DAGSTER_EXTERNAL_DEFAULT_OUTPUT_FILENAME,
    DAGSTER_EXTERNAL_DEFAULT_PORT,
    DAGSTER_EXTERNAL_ENV_KEYS,
    ExternalExecutionExtras,
    ExternalExecutionIOMode,
    SocketServerControlMessage,
)
from typing_extensions import Literal, TypeAlias

import dagster._check as check
from dagster import OpExecutionContext
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterExternalExecutionError
from dagster._core.external_execution.context import build_external_execution_context

# (host, port)
SocketAddress: TypeAlias = Tuple[str, int]
InputIOYield: TypeAlias = Tuple[Optional[int], Mapping[str, str]]
OutputIOYield: TypeAlias = InputIOYield


class ExternalExecutionTask:
    def __init__(
        self,
        command: Sequence[str],
        context: OpExecutionContext,
        extras: Optional[ExternalExecutionExtras],
        env: Optional[Mapping[str, str]] = None,
        input_mode: ExternalExecutionIOMode = ExternalExecutionIOMode.stdio,
        output_mode: ExternalExecutionIOMode = ExternalExecutionIOMode.stdio,
        input_path: Optional[str] = None,
        output_path: Optional[str] = None,
        socket_server_host: Optional[str] = None,
        socket_server_port: Optional[int] = None,
    ):
        self._command = command
        self._context = context
        self._extras = extras
        self._input_mode = input_mode
        self._output_mode = output_mode
        self._tempdir = None
        self._input_path = input_path
        self._output_path = output_path
        self._socket_server_host = socket_server_host
        self._socket_server_port = socket_server_port
        self.env = copy(env) if env is not None else {}

    def run(self) -> None:
        base_env = {
            **os.environ,
            **self.env,
            DAGSTER_EXTERNAL_ENV_KEYS["is_orchestration_active"]: "1",
            DAGSTER_EXTERNAL_ENV_KEYS["input_mode"]: self._input_mode.value,
            DAGSTER_EXTERNAL_ENV_KEYS["output_mode"]: self._output_mode.value,
        }

        with ExitStack() as stack:
            # tempdir may be accessed in input/output context managers
            self._tempdir = stack.enter_context(tempfile.TemporaryDirectory())
            if ExternalExecutionIOMode.socket in (self._input_mode, self._output_mode):
                stack.enter_context(self._socket_server_context_manager())
            stdin_fd, input_env_vars = stack.enter_context(self._input_context_manager())
            stdout_fd, output_env_vars = stack.enter_context(self._output_context_manager())

            process = Popen(
                self._command,
                stdin=stdin_fd,
                stdout=stdout_fd,
                env={**base_env, **input_env_vars, **output_env_vars},
            )
            process.wait()

            if process.returncode != 0:
                raise DagsterExternalExecutionError(
                    f"External execution process failed with code {process.returncode}"
                )

    # ########################
    # ##### IO CONTEXT MANAGERS
    # ########################

    def _input_context_manager(self) -> ContextManager[InputIOYield]:
        if self._input_mode == ExternalExecutionIOMode.stdio:
            return self._stdio_input()
        elif self._input_mode == ExternalExecutionIOMode.file:
            return self._file_input()
        elif self._input_mode == ExternalExecutionIOMode.fifo:
            return self._fifo_input()
        elif self._input_mode == ExternalExecutionIOMode.socket:
            return self._socket_input()
        else:
            check.failed(f"Unsupported input mode: {self._input_mode}")

    @contextmanager
    def _stdio_input(self) -> Iterator[InputIOYield]:
        read_fd, write_fd = os.pipe()
        self._write_input(write_fd)
        yield read_fd, {}
        os.close(read_fd)

    @contextmanager
    def _file_input(self) -> Iterator[InputIOYield]:
        path = self._prepare_io_path(self._input_path, "input")
        env = {DAGSTER_EXTERNAL_ENV_KEYS["input"]: path}
        try:
            self._write_input(path)
            yield None, env
        finally:
            os.remove(path)

    @contextmanager
    def _fifo_input(self) -> Iterator[InputIOYield]:
        path = self._prepare_io_path(self._input_path, "input")
        if not os.path.exists(path):
            os.mkfifo(path)
        try:
            # Use thread to prevent blocking
            thread = Thread(target=self._write_input, args=(path,), daemon=True)
            thread.start()
            env = {DAGSTER_EXTERNAL_ENV_KEYS["input"]: path}
            yield None, env
            thread.join()
        finally:
            os.remove(path)

    # Socket server is started/shutdown in a dedicated context manager to share logic between input
    # and output.
    @contextmanager
    def _socket_input(self) -> Iterator[InputIOYield]:
        env = {
            DAGSTER_EXTERNAL_ENV_KEYS["host"]: (
                self._socket_server_host or DAGSTER_EXTERNAL_DEFAULT_HOST
            ),
            DAGSTER_EXTERNAL_ENV_KEYS["port"]: str(
                self._socket_server_port or DAGSTER_EXTERNAL_DEFAULT_PORT
            ),
        }
        yield None, env

    def _output_context_manager(self) -> ContextManager[OutputIOYield]:
        if self._output_mode == ExternalExecutionIOMode.stdio:
            return self._stdio_output()
        elif self._output_mode == ExternalExecutionIOMode.file:
            return self._file_output()
        elif self._output_mode == ExternalExecutionIOMode.fifo:
            return self._fifo_output()
        elif self._output_mode == ExternalExecutionIOMode.socket:
            return self.socket_output()
        else:
            check.failed(f"Unsupported output mode: {self._output_mode}")

    @contextmanager
    def _stdio_output(self) -> Iterator[OutputIOYield]:
        read_fd, write_fd = os.pipe()
        is_task_complete = Event()
        thread = None
        try:
            thread = self._default_output_thread(read_fd, is_task_complete)
            yield write_fd, {}
        finally:
            os.close(write_fd)
            is_task_complete.set()
            if thread:
                thread.join()

    @contextmanager
    def _file_output(self) -> Iterator[OutputIOYield]:
        path = self._prepare_io_path(self._output_path, "output")
        env = {DAGSTER_EXTERNAL_ENV_KEYS["output"]: path}
        open(path, "w").close()  # create file
        is_task_complete = Event()
        thread = None
        try:
            thread = self._default_output_thread(path, is_task_complete)
            yield None, env
        finally:
            is_task_complete.set()
            if thread:
                thread.join()
            os.remove(path)

    @contextmanager
    def _fifo_output(self) -> Iterator[OutputIOYield]:
        path = self._prepare_io_path(self._output_path, "output")
        env = {DAGSTER_EXTERNAL_ENV_KEYS["output"]: path}
        if not os.path.exists(path):
            os.mkfifo(path)
        # We open a write file descriptor for a FIFO in the orchestration
        # process in order to keep the FIFO open for reading. Otherwise, the
        # FIFO will receive EOF after the first file descriptor writing it is
        # closed in an external process. Note that `O_RDWR` is required for
        # this call to succeed when no readers are yet available, and
        # `O_NONBLOCK` is required to prevent the `open` call from blocking.
        is_task_complete = Event()
        dummy_handle = None
        thread = None
        try:
            dummy_handle = os.open(path, os.O_RDWR | os.O_NONBLOCK)
            thread = self._default_output_thread(path, is_task_complete)
            yield None, env
        finally:
            is_task_complete.set()
            if dummy_handle:
                os.close(dummy_handle)
            if thread:
                thread.join()
            os.remove(path)

    # Socket server is started/shutdown in a dedicated context manager to share logic between input
    # and output.
    @contextmanager
    def socket_output(self) -> Iterator[OutputIOYield]:
        env = {
            DAGSTER_EXTERNAL_ENV_KEYS["host"]: (
                self._socket_server_host or DAGSTER_EXTERNAL_DEFAULT_HOST
            ),
            DAGSTER_EXTERNAL_ENV_KEYS["port"]: str(
                self._socket_server_port or DAGSTER_EXTERNAL_DEFAULT_PORT
            ),
        }
        yield None, env

    @contextmanager
    def _socket_server_context_manager(self) -> Iterator[Tuple[str, int]]:
        host = self._socket_server_host or DAGSTER_EXTERNAL_DEFAULT_HOST
        port = self._socket_server_port or DAGSTER_EXTERNAL_DEFAULT_PORT
        sockaddr = (host, port)
        thread = self._start_socket_server_thread(sockaddr)
        yield sockaddr
        self._shutdown_socket_server(sockaddr)
        thread.join()

    # ########################
    # ##### THREADED IO ROUTINES
    # ########################

    def _start_socket_server_thread(self, sockaddr: SocketAddress) -> Thread:
        is_server_started = Event()
        thread = Thread(
            target=self._start_socket_server, args=(sockaddr, is_server_started), daemon=True
        )
        thread.start()
        is_server_started.wait()
        return thread

    def _default_output_thread(
        self, path_or_fd: Union[str, int], is_task_complete: Event
    ) -> Thread:
        thread = Thread(target=self._read_output, args=(path_or_fd, is_task_complete), daemon=True)
        thread.start()
        return thread

    # Not used in socket mode
    def _write_input(self, path_or_fd: Union[str, int]) -> None:
        external_context = build_external_execution_context(self._context, self._extras)
        with open(path_or_fd, "w") as input_stream:
            json.dump(external_context, input_stream)

    # Not used in socket mode
    def _read_output(self, path_or_fd: Union[str, int], is_task_complete: Event) -> Any:
        with open(path_or_fd, "r") as output_stream:
            while True:
                line = output_stream.readline()
                if line:
                    notification = json.loads(line)
                    self.handle_notification(notification)
                elif is_task_complete.is_set():
                    break
                else:
                    time.sleep(0.01)

    # Only used in socket mode
    def _start_socket_server(self, sockaddr: SocketAddress, is_server_started: Event) -> None:
        context = build_external_execution_context(self._context, self._extras)
        handle_notification = self.handle_notification

        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                data = self.rfile.readline().strip().decode("utf-8")
                if data == SocketServerControlMessage.shutdown:
                    self.server.shutdown()
                elif data == SocketServerControlMessage.get_context:
                    response_data = f"{json.dumps(context)}\n".encode("utf-8")
                    self.wfile.write(response_data)
                elif data == SocketServerControlMessage.initiate_client_stream:
                    self.notification_stream_loop()
                else:
                    raise Exception(f"Unrecognized control message: {data}")

            def notification_stream_loop(self):
                while True:
                    data = self.rfile.readline().strip().decode("utf-8")
                    notification = json.loads(data)
                    handle_notification(notification)

        # It is essential to set `allow_reuse_address` to True here, otherwise `socket.bind` seems
        # to nondeterministically block when running multiple tests using the same address in
        # succession.
        class Server(socketserver.ThreadingTCPServer):
            allow_reuse_address = True

        with Server(sockaddr, Handler) as server:
            is_server_started.set()
            server.serve_forever()

    # Only used in socket mode
    def _shutdown_socket_server(self, sockaddr: SocketAddress) -> None:
        with socket.create_connection(sockaddr) as sock:
            sock.makefile("w").write(f"{SocketServerControlMessage.shutdown.value}\n")

    # ########################
    # ##### HANDLE NOTIFICATIONS
    # ########################

    def handle_notification(self, message: Mapping[str, Any]) -> None:
        if message["method"] == "report_asset_metadata":
            self._handle_report_asset_metadata(**message["params"])
        elif message["method"] == "report_asset_data_version":
            self._handle_report_asset_data_version(**message["params"])
        elif message["method"] == "log":
            self._handle_log(**message["params"])

    def _handle_report_asset_metadata(self, asset_key: str, label: str, value: Any) -> None:
        key = AssetKey.from_user_string(asset_key)
        output_name = self._context.output_for_asset_key(key)
        self._context.add_output_metadata({label: value}, output_name)

    def _handle_report_asset_data_version(self, asset_key: str, data_version: str) -> None:
        key = AssetKey.from_user_string(asset_key)
        self._context.set_data_version(key, DataVersion(data_version))

    def _handle_log(self, message: str, level: str = "info") -> None:
        check.str_param(message, "message")
        self._context.log.log(level, message)

    # ########################
    # ##### UTILITIES
    # ########################

    def _prepare_io_path(self, path: Optional[str], target: Literal["input", "output"]) -> str:
        if path is None:
            if target == "input":
                filename = DAGSTER_EXTERNAL_DEFAULT_INPUT_FILENAME
            else:  # output
                filename = DAGSTER_EXTERNAL_DEFAULT_OUTPUT_FILENAME
            assert self._tempdir is not None
            return os.path.join(self._tempdir, filename)
        else:
            self._validate_io_path(path, target)
            self._clear_io_path(path)
            return path

    def _validate_io_path(self, path: str, target: Literal["input", "output"]) -> None:
        dirname = os.path.dirname(path)
        check.invariant(
            os.path.isdir(dirname),
            f"{path} has been specified as `{target}_path` but directory {dirname} does not"
            " currently exist. You must create it.",
        )

    def _clear_io_path(self, path: str) -> None:
        if os.path.exists(path):
            os.remove(path)
