import json
import os
import shutil
import socket
import socketserver
import tempfile
from copy import copy
from dataclasses import dataclass
from subprocess import Popen
from threading import Event, Thread
from typing import Any, Mapping, Optional, Sequence, Tuple, Union

from dagster_external.protocol import (
    DAGSTER_EXTERNAL_DEFAULT_INPUT_FILENAME,
    DAGSTER_EXTERNAL_DEFAULT_OUTPUT_FILENAME,
    DAGSTER_EXTERNAL_DEFAULT_PORT,
    DAGSTER_EXTERNAL_ENV_KEYS,
    GET_CONTEXT_MESSAGE,
    ExternalExecutionExtras,
    ExternalExecutionIOMode,
)
from typing_extensions import Literal

import dagster._check as check
from dagster import OpExecutionContext
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.events import AssetKey
from dagster._core.external_execution.context import build_external_execution_context


@dataclass
class SocketAddress:
    host: str
    port: int


CLOSE_SOCKET_MESSAGE = "__CLOSE_SOCKET__"


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
    ):
        self._command = command
        self._context = context
        self._extras = extras
        self._input_mode = input_mode
        self._output_mode = output_mode
        self._tempdir = None
        self._input_path = input_path
        self._output_path = output_path
        self.env = copy(env) if env is not None else {}

    def run(self) -> int:
        write_target, stdin_fd, input_env_vars = self._prepare_input()
        read_target, stdout_fd, output_env_vars = self._prepare_output()

        if self._input_mode == ExternalExecutionIOMode.stdio:
            assert isinstance(write_target, int)
            input_thread = self._default_input_thread(write_target)
            input_thread.start()
        elif self._input_mode == ExternalExecutionIOMode.file:
            assert isinstance(write_target, str)
            input_thread = None
            self._write_input(write_target)
        elif self._input_mode == ExternalExecutionIOMode.fifo:
            assert isinstance(write_target, str)
            input_thread = self._default_input_thread(write_target)
            input_thread.start()
        elif self._input_mode == ExternalExecutionIOMode.socket:
            assert isinstance(write_target, SocketAddress)
            input_thread = self._start_socket_server(write_target)
        else:
            check.failed(f"Unsupported input mode: {self._input_mode}")

        if self._output_mode == ExternalExecutionIOMode.stdio:
            assert isinstance(read_target, int)
            output_thread = self._default_output_thread(read_target)
            output_thread.start()
        elif self._output_mode == ExternalExecutionIOMode.file:
            output_thread = None
        elif self._output_mode == ExternalExecutionIOMode.fifo:
            assert isinstance(read_target, str)
            output_thread = self._default_output_thread(read_target)
            output_thread.start()
        elif self._output_mode == ExternalExecutionIOMode.socket:
            assert isinstance(read_target, SocketAddress)
            # thread already exists
            if self._input_mode == ExternalExecutionIOMode.socket:
                output_thread = input_thread
            else:
                output_thread = self._start_socket_server(read_target)
        else:
            check.failed(f"Unsupported output mode: {self._output_mode}")

        process = Popen(
            self._command,
            stdin=stdin_fd,
            stdout=stdout_fd,
            env={**os.environ, **self.env, **input_env_vars, **output_env_vars},
        )
        process.wait()

        if self._input_mode == ExternalExecutionIOMode.stdio:
            assert stdin_fd is not None
            os.close(stdin_fd)
            assert input_thread is not None
            input_thread.join()
        elif self._input_mode == ExternalExecutionIOMode.file:
            pass
        elif self._input_mode == ExternalExecutionIOMode.fifo:
            assert input_thread is not None
            input_thread.join()
        elif self._input_mode == ExternalExecutionIOMode.socket:
            assert isinstance(write_target, SocketAddress)
            self._shutdown_socket_server(write_target)
            assert input_thread is not None
            input_thread.join()
        else:
            check.failed(f"Unsupported input mode: {self._input_mode}")

        if self._output_mode == ExternalExecutionIOMode.stdio:
            assert stdout_fd is not None
            os.close(stdout_fd)
            assert output_thread is not None
            output_thread.join()
        elif self._output_mode == ExternalExecutionIOMode.file:
            assert isinstance(read_target, str)
            self._read_output(read_target)
        elif self._output_mode == ExternalExecutionIOMode.fifo:
            assert output_thread is not None
            output_thread.join()
        elif self._output_mode == ExternalExecutionIOMode.socket:
            # If input_mode is socket, we will have already shut down the socket server and joined
            # the socket thread
            if self._input_mode != ExternalExecutionIOMode.socket:
                assert isinstance(read_target, SocketAddress)
                self._shutdown_socket_server(read_target)
                assert output_thread is not None
                output_thread.join()
        else:
            check.failed(f"Unsupported output mode: {self._output_mode}")

        if self._input_path:
            os.remove(self._input_path)
        if self._output_path:
            os.remove(self._output_path)
        if self._tempdir is not None:
            shutil.rmtree(self._tempdir)

        return process.returncode

    def process_notification(self, message: Mapping[str, Any]) -> None:
        if message["method"] == "report_asset_metadata":
            self._handle_report_asset_metadata(**message["params"])
        elif message["method"] == "report_asset_data_version":
            self._handle_report_asset_data_version(**message["params"])
        elif message["method"] == "log":
            self._handle_log(**message["params"])

    def _prepare_input(
        self,
    ) -> Tuple[Union[str, int, SocketAddress], Optional[int], Mapping[str, str]]:
        env = {DAGSTER_EXTERNAL_ENV_KEYS["input_mode"]: self._input_mode.value}
        if self._input_mode == ExternalExecutionIOMode.stdio:
            stdin_fd, write_target = os.pipe()
        elif self._input_mode in [ExternalExecutionIOMode.file, ExternalExecutionIOMode.fifo]:
            stdin_fd = None
            if self._input_path is None:
                write_target = os.path.join(self.tempdir, DAGSTER_EXTERNAL_DEFAULT_INPUT_FILENAME)
            else:
                self._validate_target_path(self._input_path, "input")
                self._clear_target_path(self._input_path)
                write_target = self._input_path
            if self._input_mode == ExternalExecutionIOMode.fifo and not os.path.exists(
                write_target
            ):
                os.mkfifo(write_target)
            env[DAGSTER_EXTERNAL_ENV_KEYS["input"]] = write_target
        elif self._input_mode == ExternalExecutionIOMode.socket:
            stdin_fd = None
            write_target = SocketAddress("localhost", DAGSTER_EXTERNAL_DEFAULT_PORT)

            env[DAGSTER_EXTERNAL_ENV_KEYS["host"]] = write_target.host
            env[DAGSTER_EXTERNAL_ENV_KEYS["port"]] = str(write_target.port)
        else:
            check.failed(f"Unsupported input mode: {self._input_mode}")
        return write_target, stdin_fd, env

    def _prepare_output(
        self,
    ) -> Tuple[Union[str, int, SocketAddress], Optional[int], Mapping[str, str]]:
        env = {DAGSTER_EXTERNAL_ENV_KEYS["output_mode"]: self._output_mode.value}
        if self._output_mode == ExternalExecutionIOMode.stdio:
            read_target, stdout_fd = os.pipe()
        elif self._output_mode in [ExternalExecutionIOMode.file, ExternalExecutionIOMode.fifo]:
            stdout_fd = None
            if self._output_path is None:
                read_target = os.path.join(self.tempdir, DAGSTER_EXTERNAL_DEFAULT_OUTPUT_FILENAME)
            else:
                self._validate_target_path(self._output_path, "output")
                self._clear_target_path(self._output_path)
                read_target = self._output_path
            if self._output_mode == ExternalExecutionIOMode.fifo and not os.path.exists(
                read_target
            ):
                os.mkfifo(read_target)
            env[DAGSTER_EXTERNAL_ENV_KEYS["output"]] = read_target
        elif self._output_mode == ExternalExecutionIOMode.socket:
            stdout_fd = None
            read_target = SocketAddress("localhost", DAGSTER_EXTERNAL_DEFAULT_PORT)
            env[DAGSTER_EXTERNAL_ENV_KEYS["host"]] = read_target.host
            env[DAGSTER_EXTERNAL_ENV_KEYS["port"]] = str(read_target.port)
        else:
            check.failed(f"Unsupported output mode: {self._output_mode}")
        return read_target, stdout_fd, env

    def _validate_target_path(self, path: str, target: Literal["input", "output"]) -> None:
        dirname = os.path.dirname(path)
        check.invariant(
            os.path.isdir(dirname),
            f"{path} has been specified as `{target}_path` but directory {dirname} does not"
            " currently exist. You must create it.",
        )

    def _clear_target_path(self, path: str) -> None:
        if os.path.exists(path):
            os.remove(path)

    @property
    def tempdir(self) -> str:
        if self._tempdir is None:
            self._tempdir = tempfile.mkdtemp()
        return self._tempdir

    # ########################
    # ##### THREADED IO ROUTINES
    # ########################

    def _default_input_thread(self, write_target) -> Thread:
        return Thread(target=self._write_input, args=(write_target,), daemon=True)

    def _default_output_thread(self, read_target) -> Thread:
        return Thread(target=self._read_output, args=(read_target,), daemon=True)

    # Not used in socket mode
    def _write_input(self, input_target: Union[str, int]) -> None:
        external_context = build_external_execution_context(self._context, self._extras)
        with open(input_target, "w") as input_stream:
            json.dump(external_context, input_stream)

    # Not used in socket mode
    def _read_output(self, output_target: Union[str, int]) -> Any:
        with open(output_target, "r") as output_stream:
            for line in output_stream:
                notification = json.loads(line)
                self.process_notification(notification)

    # Only used in socket mode
    def _socket_serve(self, socket_address: SocketAddress, ready_event: Event) -> None:
        context = build_external_execution_context(self._context, self._extras)

        handle_notification = self.process_notification

        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                data = self.rfile.readline().strip().decode("utf-8")
                if data == CLOSE_SOCKET_MESSAGE:
                    self.server.shutdown()
                elif data == GET_CONTEXT_MESSAGE:
                    serialized_context = json.dumps(context) + "\n"
                    self.wfile.write(serialized_context.encode("utf-8"))
                else:
                    notification = json.loads(data)
                    handle_notification(notification)

        # It is essential to set `allow_reuse_address` to True here, otherwise `socket.bind` seems
        # to nondeterministically block when running multiple tests using the same address in
        # succession.
        class Server(socketserver.ThreadingTCPServer):
            allow_reuse_address = True

        with Server((socket_address.host, socket_address.port), Handler) as server:
            ready_event.set()
            server.serve_forever()

    def _start_socket_server(self, write_target: SocketAddress) -> Thread:
        ready_event = Event()
        thread = Thread(target=self._socket_serve, args=(write_target, ready_event), daemon=True)
        thread.start()

        if not ready_event.is_set():
            ready_event.wait()

        return thread

    def _shutdown_socket_server(self, address: SocketAddress) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((address.host, address.port))
            message = CLOSE_SOCKET_MESSAGE + "\n"
            sock.sendall(message.encode("utf-8"))

    # ########################
    # ##### HANDLE NOTIFICATIONS
    # ########################

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
