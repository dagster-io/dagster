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
)

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
        input_mode: str = "stdio",
        output_mode: str = "stdio",
        input_fifo: Optional[str] = None,
        output_fifo: Optional[str] = None,
    ):
        self._command = command
        self._context = context
        self._extras = extras
        self._input_mode = input_mode
        self._output_mode = output_mode
        self._tempdir = None

        if input_mode == "fifo":
            self._validate_fifo("input", input_fifo)
        self._input_fifo = check.opt_str_param(input_fifo, "input_fifo")

        if output_mode == "fifo":
            self._validate_fifo("output", output_fifo)
        self._output_fifo = check.opt_str_param(output_fifo, "output_fifo")

        self.env = copy(env) if env is not None else {}

    def _validate_fifo(self, input_output: str, value: Optional[str]) -> None:
        if value is None or not os.path.exists(value):
            check.failed(
                f'Must provide pre-existing `{input_output}_fifo` when using "fifo"'
                f' `{input_output}_mode`. Set `{input_output}_mode="temp_fifo"` to use a'
                " system-generated temporary FIFO."
            )

    def run(self) -> int:
        write_target, stdin_fd, input_env_vars = self._prepare_input()
        read_target, stdout_fd, output_env_vars = self._prepare_output()

        input_thread = Thread(target=self._write_input, args=(write_target,), daemon=True)
        output_thread = Thread(target=self._read_output, args=(read_target,), daemon=True)

        # Synchronously write the file in advance if using temp_file mode
        if self._input_mode == "temp_file":
            input_thread.run()
        else:
            input_thread.start()

        # If we're using an output tempfile, we won't read it until the process is done
        if self._output_mode != "temp_file":
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
        if self._input_mode != "temp_file":
            input_thread.join()

        # Read tempfile output synchronously ofter everything the process has finished
        if self._output_mode == "temp_file":
            output_thread.run()
        else:
            output_thread.join()

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
        if self._input_mode == "stdio":
            stdin_fd, write_target = os.pipe()
            env = {
                DAGSTER_EXTERNAL_ENV_KEYS["input_mode"]: "stdio",
            }
        elif self._input_mode == "temp_file":
            stdin_fd = None
            write_target = os.path.join(self.tempdir, DAGSTER_EXTERNAL_DEFAULT_INPUT_FILENAME)
            env = {
                DAGSTER_EXTERNAL_ENV_KEYS["input_mode"]: "temp_file",
                DAGSTER_EXTERNAL_ENV_KEYS["input"]: write_target,
            }
        elif self._input_mode == "fifo":
            assert self._input_fifo is not None
            stdin_fd = None
            write_target = self._input_fifo
            env = {
                DAGSTER_EXTERNAL_ENV_KEYS["input_mode"]: "fifo",
                DAGSTER_EXTERNAL_ENV_KEYS["input"]: self._input_fifo,
            }
        elif self._input_mode == "temp_fifo":
            stdin_fd = None
            write_target = os.path.join(self.tempdir, DAGSTER_EXTERNAL_DEFAULT_INPUT_FILENAME)
            os.mkfifo(write_target)
            write_target = write_target
            env = {
                DAGSTER_EXTERNAL_ENV_KEYS["input_mode"]: "fifo",
                DAGSTER_EXTERNAL_ENV_KEYS["input"]: write_target,
            }
        else:
            check.failed(f"Unsupported input mode: {self._input_mode}")
        return write_target, stdin_fd, env

    def _prepare_output(self) -> Tuple[Union[str, int], Optional[int], Mapping[str, str]]:
        if self._output_mode == "stdio":
            read_target, stdout_fd = os.pipe()
            env = {
                DAGSTER_EXTERNAL_ENV_KEYS["output_mode"]: "stdio",
            }
        elif self._output_mode == "temp_file":
            stdout_fd = None
            read_target = os.path.join(self.tempdir, DAGSTER_EXTERNAL_DEFAULT_OUTPUT_FILENAME)
            env = {
                DAGSTER_EXTERNAL_ENV_KEYS["output_mode"]: "temp_file",
                DAGSTER_EXTERNAL_ENV_KEYS["output"]: read_target,
            }
        elif self._output_mode == "fifo":
            assert self._output_fifo is not None
            stdout_fd = None
            read_target = self._output_fifo
            env = {
                DAGSTER_EXTERNAL_ENV_KEYS["output_mode"]: "fifo",
                DAGSTER_EXTERNAL_ENV_KEYS["output"]: self._output_fifo,
            }
        elif self._output_mode == "temp_fifo":
            stdout_fd = None
            read_target = os.path.join(self.tempdir, DAGSTER_EXTERNAL_DEFAULT_OUTPUT_FILENAME)
            os.mkfifo(read_target)
            env = {
                DAGSTER_EXTERNAL_ENV_KEYS["output_mode"]: "fifo",
                DAGSTER_EXTERNAL_ENV_KEYS["output"]: read_target,
            }
        else:
            check.failed(f"Unsupported output mode: {self._output_mode}")
        return read_target, stdout_fd, env

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
