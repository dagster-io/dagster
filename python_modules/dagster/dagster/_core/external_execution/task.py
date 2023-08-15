import json
import os
import shutil
import tempfile
from copy import copy
from subprocess import Popen
from threading import Thread
from typing import Any, Mapping, Optional, Sequence, Tuple, Union

from dagster_external.protocol import (
    DAGSTER_EXTERNAL_DEFAULT_INPUT_FILENAME,
    DAGSTER_EXTERNAL_DEFAULT_OUTPUT_FILENAME,
    DAGSTER_EXTERNAL_ENV_KEYS,
    ExternalExecutionExtras,
    ExternalExecutionIOMode,
)
from typing_extensions import Literal

import dagster._check as check
from dagster import OpExecutionContext
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.events import AssetKey
from dagster._core.external_execution.context import build_external_execution_context


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

        input_thread = Thread(target=self._write_input, args=(write_target,), daemon=True)
        output_thread = Thread(target=self._read_output, args=(read_target,), daemon=True)

        # Synchronously write the file in advance if using file mode
        if self._input_mode == ExternalExecutionIOMode.file:
            input_thread.run()
        else:
            input_thread.start()

        # If we're using an output file, we won't read it until the process is done
        if self._output_mode != ExternalExecutionIOMode.file:
            output_thread.start()

        process = Popen(
            self._command,
            stdin=stdin_fd,
            stdout=stdout_fd,
            env={**os.environ, **self.env, **input_env_vars, **output_env_vars},
        )

        if stdin_fd is not None:
            os.close(stdin_fd)
        if stdout_fd is not None:
            os.close(stdout_fd)

        process.wait()

        # Tempfile input will have been synchronously written without a living thread
        if self._input_mode != ExternalExecutionIOMode.file:
            input_thread.join()

        # Read tempfile output synchronously ofter everything the process has finished
        if self._output_mode == ExternalExecutionIOMode.file:
            output_thread.run()
        else:
            output_thread.join()

        if self._input_path:
            os.remove(self._input_path)
        if self._output_path:
            os.remove(self._output_path)
        if self._tempdir is not None:
            shutil.rmtree(self._tempdir)

        return process.returncode

    def _write_input(self, input_target: Union[str, int]) -> None:
        external_context = build_external_execution_context(self._context, self._extras)
        with open(input_target, "w") as input_stream:
            json.dump(external_context, input_stream)

    def _read_output(self, output_target: Union[str, int]) -> Any:
        with open(output_target, "r") as output_stream:
            for line in output_stream:
                message = json.loads(line)
                if message["method"] == "report_asset_metadata":
                    self._handle_report_asset_metadata(**message["params"])
                elif message["method"] == "report_asset_data_version":
                    self._handle_report_asset_data_version(**message["params"])
                elif message["method"] == "log":
                    self._handle_log(**message["params"])

    def _prepare_input(self) -> Tuple[Union[str, int], Optional[int], Mapping[str, str]]:
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
        else:
            check.failed(f"Unsupported input mode: {self._input_mode}")
        return write_target, stdin_fd, env

    def _prepare_output(self) -> Tuple[Union[str, int], Optional[int], Mapping[str, str]]:
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
