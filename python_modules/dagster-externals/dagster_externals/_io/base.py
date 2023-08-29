import datetime
import json
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from io import StringIO
from threading import Event, Thread
from typing import Iterator, List, TypeVar

from .._protocol import (
    ExternalExecutionContextData,
    ExternalExecutionMessage,
    ExternalExecutionParams,
)


class ExternalExecutionContextLoader(ABC):
    @abstractmethod
    @contextmanager
    def load_context(
        self, params: ExternalExecutionParams
    ) -> Iterator[ExternalExecutionContextData]:
        ...


T_MessageChannel = TypeVar("T_MessageChannel", bound="ExternalExecutionMessageWriterChannel")


class ExternalExecutionMessageWriter(ABC, Generic[T_MessageChannel]):
    @abstractmethod
    @contextmanager
    def open(self, params: ExternalExecutionParams) -> Iterator[T_MessageChannel]:
        ...


class ExternalExecutionMessageWriterChannel(ABC, Generic[T_MessageChannel]):
    @abstractmethod
    def write_message(self, message: ExternalExecutionMessage) -> None:
        ...


class ExternalExecutionParamLoader(ABC):
    @abstractmethod
    def load_context_params(self) -> ExternalExecutionParams:
        ...

    @abstractmethod
    def load_messages_params(self) -> ExternalExecutionParams:
        ...


class ExternalExecutionBlobStoreMessageWriter(ABC):
    interval: int
    max_chunk_size: int
    buffer: List[ExternalExecutionMessage]
    counter: int

    def __init__(self, *, interval: int = 10):
        self.interval = interval
        self.buffer = []
        self.counter = 1

    @contextmanager
    def setup(self, params: ExternalExecutionParams) -> Iterator[None]:
        self.set_params(params)
        thread = None
        is_task_complete = Event()
        try:
            thread = Thread(target=self.writer_thread, args=(is_task_complete,), daemon=True)
            thread.start()
            yield
        finally:
            is_task_complete.set()
            if thread:
                thread.join()

    def write_message(self, message: ExternalExecutionMessage) -> None:
        self.buffer.append(message)

    def write_messages_chunk(self, index: int) -> None:
        payload = "\n".join([json.dumps(message) for message in self.buffer])
        self.upload_messages_chunk(StringIO(payload), index)

    @abstractmethod
    def set_params(self, params: ExternalExecutionParams) -> None:
        ...

    @abstractmethod
    def upload_messages_chunk(self, payload: StringIO, index: int) -> None:
        ...

    def writer_thread(self, is_task_complete: Event) -> None:
        start_or_last_upload = datetime.datetime.now()
        while True:
            num_pending = len(self.buffer)
            now = datetime.datetime.now()
            if num_pending == 0 and is_task_complete.is_set():
                break
            elif is_task_complete.is_set() or (now - start_or_last_upload).seconds > self.interval:
                self.write_messages_chunk(self.counter)
                start_or_last_upload = now
                self.buffer.clear()
                self.counter += 1
            time.sleep(1)
