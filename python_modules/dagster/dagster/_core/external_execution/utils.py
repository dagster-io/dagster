import datetime
import json
import os
import time
from abc import abstractmethod
from contextlib import contextmanager
from threading import Event, Thread
from typing import TYPE_CHECKING, Iterator, Mapping, Optional

from dagster_externals import DAGSTER_EXTERNALS_ENV_KEYS, ExternalExecutionParams, encode_env_var

from dagster._core.external_execution.resource import (
    ExternalExecutionContextInjector,
    ExternalExecutionMessageReader,
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
        yield {"data": context.get_data()}


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
                target=self._reader_thread, args=(context, is_task_complete), daemon=True
            )
            thread.start()
            yield {"path": self._path}
        finally:
            is_task_complete.set()
            if os.path.exists(self._path):
                os.remove(self._path)
            if thread:
                thread.join()

    def _reader_thread(
        self, context: "ExternalExecutionOrchestrationContext", is_resource_complete: Event
    ) -> None:
        for line in tail_file(self._path, lambda: is_resource_complete.is_set()):
            message = json.loads(line)
            context.handle_message(message)


class ExternalExecutionBlobStoreMessageReader(ExternalExecutionMessageReader):
    interval: float
    counter: int

    def __init__(self, interval: float = 10):
        self.interval = interval
        self.counter = 1

    @contextmanager
    def read_messages(
        self,
        context: "ExternalExecutionOrchestrationContext",
    ) -> Iterator[ExternalExecutionParams]:
        with self.setup():
            is_task_complete = Event()
            thread = None
            try:
                thread = Thread(
                    target=self._reader_thread,
                    args=(
                        context,
                        is_task_complete,
                    ),
                    daemon=True,
                )
                thread.start()
                yield self.get_params()
            finally:
                is_task_complete.set()
                if thread:
                    thread.join()

    @contextmanager
    def setup(self) -> Iterator[None]:
        yield

    @abstractmethod
    def get_params(self) -> ExternalExecutionParams:
        ...

    @abstractmethod
    def download_messages_chunk(self, index: int) -> Optional[str]:
        ...

    def _reader_thread(
        self, context: "ExternalExecutionOrchestrationContext", is_task_complete: Event
    ) -> None:
        start_or_last_download = datetime.datetime.now()
        while True:
            now = datetime.datetime.now()
            if (now - start_or_last_download).seconds > self.interval or is_task_complete.is_set():
                chunk = self.download_messages_chunk(self.counter)
                start_or_last_download = now
                if chunk:
                    for line in chunk.split("\n"):
                        message = json.loads(line)
                        context.handle_message(message)
                    self.counter += 1
                elif is_task_complete.is_set():
                    break
            time.sleep(1)


def io_params_as_env_vars(
    context_injector_params: ExternalExecutionParams, message_reader_params: ExternalExecutionParams
) -> Mapping[str, str]:
    return {
        DAGSTER_EXTERNALS_ENV_KEYS["context"]: encode_env_var(context_injector_params),
        DAGSTER_EXTERNALS_ENV_KEYS["messages"]: encode_env_var(message_reader_params),
    }
