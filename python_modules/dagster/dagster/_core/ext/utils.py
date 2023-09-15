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

from dagster_ext import (
    ExtContextData,
    ExtDefaultContextLoader,
    ExtDefaultMessageWriter,
    ExtExtras,
    ExtParams,
)

from dagster import OpExecutionContext
from dagster._core.ext.client import (
    ExtContextInjector,
    ExtMessageReader,
)
from dagster._core.ext.context import (
    ExtMessageHandler,
    ExtOrchestrationContext,
    build_external_execution_context_data,
)
from dagster._utils import tail_file

_CONTEXT_INJECTOR_FILENAME = "context"
_MESSAGE_READER_FILENAME = "messages"


class ExtFileContextInjector(ExtContextInjector):
    def __init__(self, path: str):
        self._path = path

    @contextmanager
    def inject_context(self, context_data: "ExtContextData") -> Iterator[ExtParams]:
        with open(self._path, "w") as input_stream:
            json.dump(context_data, input_stream)
        try:
            yield {ExtDefaultContextLoader.FILE_PATH_KEY: self._path}
        finally:
            if os.path.exists(self._path):
                os.remove(self._path)


class ExtTempFileContextInjector(ExtContextInjector):
    @contextmanager
    def inject_context(self, context: "ExtContextData") -> Iterator[ExtParams]:
        with tempfile.TemporaryDirectory() as tempdir:
            with ExtFileContextInjector(
                os.path.join(tempdir, _CONTEXT_INJECTOR_FILENAME)
            ).inject_context(context) as params:
                yield params


class ExtEnvContextInjector(ExtContextInjector):
    @contextmanager
    def inject_context(
        self,
        context_data: "ExtContextData",
    ) -> Iterator[ExtParams]:
        yield {ExtDefaultContextLoader.DIRECT_KEY: context_data}


class ExtFileMessageReader(ExtMessageReader):
    def __init__(self, path: str):
        self._path = path

    @contextmanager
    def read_messages(
        self,
        handler: "ExtMessageHandler",
    ) -> Iterator[ExtParams]:
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

    def _reader_thread(self, handler: "ExtMessageHandler", is_resource_complete: Event) -> None:
        for line in tail_file(self._path, lambda: is_resource_complete.is_set()):
            message = json.loads(line)
            handler.handle_message(message)


class ExtTempFileMessageReader(ExtMessageReader):
    @contextmanager
    def read_messages(
        self,
        handler: "ExtMessageHandler",
    ) -> Iterator[ExtParams]:
        with tempfile.TemporaryDirectory() as tempdir:
            with ExtFileMessageReader(
                os.path.join(tempdir, _CONTEXT_INJECTOR_FILENAME)
            ).read_messages(handler) as params:
                yield params


class ExtBlobStoreMessageReader(ExtMessageReader):
    interval: float
    counter: int

    def __init__(self, interval: float = 10):
        self.interval = interval
        self.counter = 1

    @contextmanager
    def read_messages(
        self,
        handler: "ExtMessageHandler",
    ) -> Iterator[ExtParams]:
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
    def get_params(self) -> Iterator[ExtParams]:
        ...

    @abstractmethod
    def download_messages_chunk(self, index: int, params: ExtParams) -> Optional[str]:
        ...

    def _reader_thread(
        self, handler: "ExtMessageHandler", params: ExtParams, is_task_complete: Event
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


def extract_message_or_forward_to_stdout(handler: "ExtMessageHandler", log_line: str):
    # exceptions as control flow, you love to see it
    try:
        message = json.loads(log_line)
        # need better message check
        if message.keys() == {"method", "params"}:
            handler.handle_message(message)
    except Exception:
        # move non-message logs in to stdout for compute log capture
        sys.stdout.writelines((log_line, "\n"))


@contextmanager
def ext_protocol(
    context: OpExecutionContext,
    context_injector: ExtContextInjector,
    message_reader: ExtMessageReader,
    extras: Optional[ExtExtras] = None,
) -> Iterator[ExtOrchestrationContext]:
    """Enter the context managed context injector and message reader that power the EXT protocol and receive the environment variables
    that need to be provided to the external process.
    """
    context_data = build_external_execution_context_data(context, extras)
    msg_handler = ExtMessageHandler(context)
    with context_injector.inject_context(
        context_data,
    ) as ci_params, message_reader.read_messages(
        msg_handler,
    ) as mr_params:
        yield ExtOrchestrationContext(
            context_data=context_data,
            message_handler=msg_handler,
            context_injector_params=ci_params,
            message_reader_params=mr_params,
        )
