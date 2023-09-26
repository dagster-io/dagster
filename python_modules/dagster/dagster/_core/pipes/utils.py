import datetime
import json
import os
import sys
import tempfile
import time
from abc import abstractmethod
from contextlib import contextmanager
from threading import Event, Thread
from typing import Iterator, Optional

from dagster_pipes import (
    PIPES_PROTOCOL_VERSION_FIELD,
    DefaultPipesContextLoader,
    ExtDefaultMessageWriter,
    PipesContextData,
    PipesExtras,
    PipesParams,
)

from dagster import (
    OpExecutionContext,
    _check as check,
)
from dagster._core.pipes.client import (
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.context import (
    PipesMessageHandler,
    PipesSession,
    build_external_execution_context_data,
)
from dagster._utils import tail_file

_CONTEXT_INJECTOR_FILENAME = "context"
_MESSAGE_READER_FILENAME = "messages"


class PipesFileContextInjector(PipesContextInjector):
    def __init__(self, path: str):
        self._path = check.str_param(path, "path")

    @contextmanager
    def inject_context(self, context_data: "PipesContextData") -> Iterator[PipesParams]:
        with open(self._path, "w") as input_stream:
            json.dump(context_data, input_stream)
        try:
            yield {DefaultPipesContextLoader.FILE_PATH_KEY: self._path}
        finally:
            if os.path.exists(self._path):
                os.remove(self._path)


class PipesTempFileContextInjector(PipesContextInjector):
    @contextmanager
    def inject_context(self, context: "PipesContextData") -> Iterator[PipesParams]:
        with tempfile.TemporaryDirectory() as tempdir:
            with PipesFileContextInjector(
                os.path.join(tempdir, _CONTEXT_INJECTOR_FILENAME)
            ).inject_context(context) as params:
                yield params


class PipesEnvContextInjector(PipesContextInjector):
    @contextmanager
    def inject_context(
        self,
        context_data: "PipesContextData",
    ) -> Iterator[PipesParams]:
        yield {DefaultPipesContextLoader.DIRECT_KEY: context_data}


class PipesFileMessageReader(PipesMessageReader):
    def __init__(self, path: str):
        self._path = check.str_param(path, "path")

    @contextmanager
    def read_messages(
        self,
        handler: "PipesMessageHandler",
    ) -> Iterator[PipesParams]:
        is_task_complete = Event()
        thread = None
        try:
            open(self._path, "w").close()  # create file
            thread = Thread(
                target=self._reader_thread, args=(handler, is_task_complete), daemon=True
            )
            thread.start()
            yield {ExtDefaultMessageWriter.FILE_PATH_KEY: self._path}
        finally:
            is_task_complete.set()
            if os.path.exists(self._path):
                os.remove(self._path)
            if thread:
                thread.join()

    def _reader_thread(self, handler: "PipesMessageHandler", is_resource_complete: Event) -> None:
        for line in tail_file(self._path, lambda: is_resource_complete.is_set()):
            message = json.loads(line)
            handler.handle_message(message)


class PipesTempFileMessageReader(PipesMessageReader):
    @contextmanager
    def read_messages(
        self,
        handler: "PipesMessageHandler",
    ) -> Iterator[PipesParams]:
        with tempfile.TemporaryDirectory() as tempdir:
            with PipesFileMessageReader(
                os.path.join(tempdir, _MESSAGE_READER_FILENAME)
            ).read_messages(handler) as params:
                yield params


class PipesBlobStoreMessageReader(PipesMessageReader):
    interval: float
    counter: int

    def __init__(self, interval: float = 10):
        self.interval = interval
        self.counter = 1

    @contextmanager
    def read_messages(
        self,
        handler: "PipesMessageHandler",
    ) -> Iterator[PipesParams]:
        with self.get_params() as params:
            is_task_complete = Event()
            thread = None
            try:
                thread = Thread(
                    target=self._reader_thread,
                    args=(
                        handler,
                        params,
                        is_task_complete,
                    ),
                    daemon=True,
                )
                thread.start()
                yield params
            finally:
                is_task_complete.set()
                if thread:
                    thread.join()

    @abstractmethod
    @contextmanager
    def get_params(self) -> Iterator[PipesParams]: ...

    @abstractmethod
    def download_messages_chunk(self, index: int, params: PipesParams) -> Optional[str]: ...

    def _reader_thread(
        self, handler: "PipesMessageHandler", params: PipesParams, is_task_complete: Event
    ) -> None:
        start_or_last_download = datetime.datetime.now()
        while True:
            now = datetime.datetime.now()
            if (now - start_or_last_download).seconds > self.interval or is_task_complete.is_set():
                chunk = self.download_messages_chunk(self.counter, params)
                start_or_last_download = now
                if chunk:
                    for line in chunk.split("\n"):
                        message = json.loads(line)
                        handler.handle_message(message)
                    self.counter += 1
                elif is_task_complete.is_set():
                    break
            time.sleep(1)


def extract_message_or_forward_to_stdout(handler: "PipesMessageHandler", log_line: str):
    # exceptions as control flow, you love to see it
    try:
        message = json.loads(log_line)
        if PIPES_PROTOCOL_VERSION_FIELD in message.keys():
            handler.handle_message(message)
    except Exception:
        # move non-message logs in to stdout for compute log capture
        sys.stdout.writelines((log_line, "\n"))


_FAIL_TO_YIELD_ERROR_MESSAGE = (
    "Did you forget to `yield from pipes_session.get_results()`? `get_results` should be called"
    " once after the `open_pipes_session` block has exited to yield any remaining buffered results."
)


@contextmanager
def open_pipes_session(
    context: OpExecutionContext,
    context_injector: PipesContextInjector,
    message_reader: PipesMessageReader,
    extras: Optional[PipesExtras] = None,
) -> Iterator[PipesSession]:
    """Enter the context managed context injector and message reader that power the EXT protocol and receive the environment variables
    that need to be provided to the external process.
    """
    # This will trigger an error if expected outputs are not yielded
    context.set_requires_typed_event_stream(error_message=_FAIL_TO_YIELD_ERROR_MESSAGE)
    context_data = build_external_execution_context_data(context, extras)
    message_handler = PipesMessageHandler(context)
    with context_injector.inject_context(
        context_data
    ) as ci_params, message_handler.handle_messages(message_reader) as mr_params:
        yield PipesSession(
            context_data=context_data,
            message_handler=message_handler,
            context_injector_params=ci_params,
            message_reader_params=mr_params,
        )
