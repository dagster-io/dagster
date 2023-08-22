import json
import os
import tempfile
import time
from abc import abstractmethod
from contextlib import ExitStack
from dataclasses import dataclass, field
from threading import Event, Thread
from typing import (
    Any,
    ContextManager,
    Dict,
    Generic,
    Mapping,
    Optional,
    Tuple,
    Union,
)

from dagster_external.protocol import (
    DAGSTER_EXTERNAL_DEFAULT_INPUT_FILENAME,
    DAGSTER_EXTERNAL_DEFAULT_OUTPUT_FILENAME,
    DAGSTER_EXTERNAL_ENV_KEYS,
    ExternalExecutionExtras,
)
from typing_extensions import Literal, TypeAlias, TypeVar

import dagster._check as check
from dagster import OpExecutionContext
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.events import AssetKey
from dagster._core.external_execution.context import build_external_execution_context

# (host, port)
SocketAddress: TypeAlias = Tuple[str, int]
InputIOYield: TypeAlias = Tuple[Optional[int], Mapping[str, str]]
OutputIOYield: TypeAlias = InputIOYield


@dataclass
class ExternalTaskParams:
    pass


@dataclass
class ExternalTaskIOParams:
    env: Dict[str, str] = field(default_factory=dict)


T_TaskParams = TypeVar("T_TaskParams")
T_TaskIOParams = TypeVar("T_TaskIOParams", bound=ExternalTaskIOParams)


class ExternalExecutionTask(Generic[T_TaskParams, T_TaskIOParams]):
    def __init__(
        self,
        context: OpExecutionContext,
        extras: Optional[ExternalExecutionExtras],
        input_path: Optional[str] = None,
        output_path: Optional[str] = None,
    ):
        self._context = context
        self._extras = extras
        self._input_path = input_path
        self._output_path = output_path

    def run(self, params: T_TaskParams) -> None:
        with ExitStack() as stack:
            tempdir = stack.enter_context(tempfile.TemporaryDirectory())
            input_params = stack.enter_context(self._input_context_manager(tempdir, params))
            output_params = stack.enter_context(self._output_context_manager(tempdir, params))
            self._launch(self.get_base_env(), params, input_params, output_params)

    def get_base_env(self) -> Mapping[str, str]:
        return {
            **os.environ,
            DAGSTER_EXTERNAL_ENV_KEYS["is_orchestration_active"]: "1",
        }

    # ########################
    # ##### PLUG POINTS
    # ########################

    @abstractmethod
    def _input_context_manager(
        self, tempdir: str, params: T_TaskParams
    ) -> ContextManager[T_TaskIOParams]:
        ...

    @abstractmethod
    def _output_context_manager(
        self, tempdir: str, params: T_TaskParams
    ) -> ContextManager[T_TaskIOParams]:
        ...

    @abstractmethod
    def _launch(
        self,
        base_env: Mapping[str, str],
        params: T_TaskParams,
        input_params: T_TaskIOParams,
        output_params: T_TaskIOParams,
    ) -> None:
        ...

    # ########################
    # ##### WRITE INPUT
    # ########################

    def _write_input(self, path_or_fd: Union[str, int]) -> None:
        external_context = build_external_execution_context(self._context, self._extras)
        with open(path_or_fd, "w") as input_stream:
            json.dump(external_context, input_stream)

    # ########################
    # ##### READ OUTPUT
    # ########################

    def _start_output_thread(self, path_or_fd: Union[str, int], is_task_complete: Event) -> Thread:
        thread = Thread(target=self._read_output, args=(path_or_fd, is_task_complete), daemon=True)
        thread.start()
        return thread

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

    def _prepare_io_path(
        self, path: Optional[str], target: Literal["input", "output"], tempdir: Optional[str]
    ) -> str:
        if path is None:
            if target == "input":
                filename = DAGSTER_EXTERNAL_DEFAULT_INPUT_FILENAME
            else:  # output
                filename = DAGSTER_EXTERNAL_DEFAULT_OUTPUT_FILENAME
            assert tempdir is not None, "Must define tempdir when path is None"
            return os.path.join(tempdir, filename)
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
