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


def get_file_context_injector(path: str) -> ExternalExecutionContextInjector:
    @contextmanager
    def context_injector(
        context: "ExternalExecutionOrchestrationContext",
    ) -> Iterator[ExternalExecutionParams]:
        with open(path, "w") as input_stream:
            json.dump(context.get_data(), input_stream)
        try:
            yield {"path": path}
        finally:
            if os.path.exists(path):
                os.remove(path)

    return context_injector


def get_env_context_injector() -> ExternalExecutionContextInjector:
    @contextmanager
    def context_injector(
        context: "ExternalExecutionOrchestrationContext",
    ) -> Iterator[ExternalExecutionParams]:
        yield {"context_data": context.get_data()}

    return context_injector


def get_file_message_reader(path: str) -> ExternalExecutionMessageReader:
    @contextmanager
    def message_reader(
        context: "ExternalExecutionOrchestrationContext",
    ) -> Iterator[ExternalExecutionParams]:
        is_task_complete = Event()
        thread = None
        try:
            open(path, "w").close()  # create file
            thread = Thread(
                target=_read_messages, args=(context, path, is_task_complete), daemon=True
            )
            thread.start()
            yield {"path": path}
        finally:
            is_task_complete.set()
            if os.path.exists(path):
                os.remove(path)
            if thread:
                thread.join()

    return message_reader


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
