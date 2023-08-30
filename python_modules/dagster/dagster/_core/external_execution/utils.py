import json
import os
from contextlib import contextmanager
from threading import Event, Thread
from typing import TYPE_CHECKING, Iterator, Mapping

from dagster_externals import DAGSTER_EXTERNALS_ENV_KEYS, encode_env_var

from dagster._core.external_execution.resource import (
    ExternalExecutionContextInjector,
    ExternalExecutionMessageReader,
    ExternalExecutionParams,
)
from dagster._utils import tail_file

if TYPE_CHECKING:
    from dagster._core.external_execution.context import ExternalExecutionOrchestrationContext


class ExternalExecutionFileContextInjector(ExternalExecutionContextInjector):
    def __init__(self, path: str):
        self._path = path

    @contextmanager
    def inject_context(
        self, context: "ExternalExecutionOrchestrationContext"
    ) -> Iterator[ExternalExecutionParams]:
        with open(self._path, "w") as input_stream:
            json.dump(context.get_data(), input_stream)
        try:
            yield {"path": self._path}
        finally:
            if os.path.exists(self._path):
                os.remove(self._path)


class ExternalExecutionEnvContextInjector(ExternalExecutionContextInjector):
    @contextmanager
    def inject_context(
        self,
        context: "ExternalExecutionOrchestrationContext",
    ) -> Iterator[ExternalExecutionParams]:
        yield {"context_data": context.get_data()}


class ExternalExecutionFileMessageReader(ExternalExecutionMessageReader):
    def __init__(self, path: str):
        self._path = path

    @contextmanager
    def read_messages(
        self,
        context: "ExternalExecutionOrchestrationContext",
    ) -> Iterator[ExternalExecutionParams]:
        is_task_complete = Event()
        thread = None
        try:
            open(self._path, "w").close()  # create file
            thread = Thread(
                target=_read_messages, args=(context, self._path, is_task_complete), daemon=True
            )
            thread.start()
            yield {"path": self._path}
        finally:
            is_task_complete.set()
            if os.path.exists(self._path):
                os.remove(self._path)
            if thread:
                thread.join()


def _read_messages(
    context: "ExternalExecutionOrchestrationContext", path: str, is_resource_complete: Event
) -> None:
    for line in tail_file(path, lambda: is_resource_complete.is_set()):
        message = json.loads(line)
        context.handle_message(message)


def io_params_as_env_vars(
    context_injector_params: ExternalExecutionParams, message_reader_params: ExternalExecutionParams
) -> Mapping[str, str]:
    return {
        DAGSTER_EXTERNALS_ENV_KEYS["context"]: encode_env_var(context_injector_params),
        DAGSTER_EXTERNALS_ENV_KEYS["messages"]: encode_env_var(message_reader_params),
    }
