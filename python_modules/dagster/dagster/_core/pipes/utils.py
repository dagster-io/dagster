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
    PipesContextData,
    PipesDefaultContextLoader,
    PipesDefaultMessageWriter,
    PipesExtras,
    PipesParams,
)

from dagster import (
    OpExecutionContext,
    _check as check,
)
from dagster._annotations import experimental
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


@experimental
class PipesFileContextInjector(PipesContextInjector):
    """Context injector that injects context data into the external process by writing it to a
    specified file.

    Args:
        path (str): The path of a file to which to write context data. The file will be deleted on
            close of the pipes session.
    """

    def __init__(self, path: str):
        self._path = check.str_param(path, "path")

    @contextmanager
    def inject_context(self, context_data: "PipesContextData") -> Iterator[PipesParams]:
        """Inject context to external environment by writing it to a file as JSON and exposing the
        path to the file.

        Args:
            context_data (PipesContextData): The context data to inject.

        Yields:
            PipesParams: A dict of parameters that can be used by the external process to locate and
            load the injected context data.
        """
        with open(self._path, "w") as input_stream:
            json.dump(context_data, input_stream)
        try:
            yield {PipesDefaultContextLoader.FILE_PATH_KEY: self._path}
        finally:
            if os.path.exists(self._path):
                os.remove(self._path)


@experimental
class PipesTempFileContextInjector(PipesContextInjector):
    """Context injector that injects context data into the external process by writing it to an
    automatically-generated temporary file.
    """

    @contextmanager
    def inject_context(self, context: "PipesContextData") -> Iterator[PipesParams]:
        """Inject context to external environment by writing it to an automatically-generated
        temporary file as JSON and exposing the path to the file.

        Args:
            context_data (PipesContextData): The context data to inject.

        Yields:
            PipesParams: A dict of parameters that can be used by the external process to locate and
            load the injected context data.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            with PipesFileContextInjector(
                os.path.join(tempdir, _CONTEXT_INJECTOR_FILENAME)
            ).inject_context(context) as params:
                yield params


class PipesEnvContextInjector(PipesContextInjector):
    """Context injector that injects context data into the external process by injecting it directly into the external process environment."""

    @contextmanager
    def inject_context(
        self,
        context_data: "PipesContextData",
    ) -> Iterator[PipesParams]:
        """Inject context to external environment by embedding directly in the parameters that will
        be passed to the external process (typically as environment variables).

        Args:
            context_data (PipesContextData): The context data to inject.

        Yields:
            PipesParams: A dict of parameters that can be used by the external process to locate and
            load the injected context data.
        """
        yield {PipesDefaultContextLoader.DIRECT_KEY: context_data}


@experimental
class PipesFileMessageReader(PipesMessageReader):
    """Message reader that reads messages by tailing a specified file.

    Args:
        path (str): The path of the file to which messages will be written. The file will be deleted
            on close of the pipes session.
    """

    def __init__(self, path: str):
        self._path = check.str_param(path, "path")

    @contextmanager
    def read_messages(
        self,
        handler: "PipesMessageHandler",
    ) -> Iterator[PipesParams]:
        """Set up a thread to read streaming messages from teh external process by tailing the
        target file.

        Args:
            handler (PipesMessageHandler): object to process incoming messages

        Yields:
            PipesParams: A dict of parameters that specifies where a pipes process should write
            pipes protocol messages.
        """
        is_task_complete = Event()
        thread = None
        try:
            open(self._path, "w").close()  # create file
            thread = Thread(
                target=self._reader_thread, args=(handler, is_task_complete), daemon=True
            )
            thread.start()
            yield {PipesDefaultMessageWriter.FILE_PATH_KEY: self._path}
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


@experimental
class PipesTempFileMessageReader(PipesMessageReader):
    """Message reader that reads messages by tailing an automatically-generated temporary file."""

    @contextmanager
    def read_messages(
        self,
        handler: "PipesMessageHandler",
    ) -> Iterator[PipesParams]:
        """Set up a thread to read streaming messages from the external process by an
        automatically-generated temporary file.

        Args:
            handler (PipesMessageHandler): object to process incoming messages

        Yields:
            PipesParams: A dict of parameters that specifies where a pipes process should write
            pipes protocol messages.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            with PipesFileMessageReader(
                os.path.join(tempdir, _MESSAGE_READER_FILENAME)
            ).read_messages(handler) as params:
                yield params


class PipesBlobStoreMessageReader(PipesMessageReader):
    """Message reader that reads a sequence of message chunks written by an external process into a
    blob store such as S3, Azure blob storage, or GCS.

    The reader maintains a counter, starting at 1, that is synchronized with a message writer in
    some pipes process. The reader starts a thread that periodically attempts to read a chunk
    indexed by the counter at some location expected to be written by the pipes process. The chunk
    should be a file with each line corresponding to a JSON-encoded pipes message. When a chunk is
    successfully read, the messages are processed and the counter is incremented. The
    :py:class:`PipesBlobStoreMessageWriter` on the other end is expected to similarly increment a
    counter (starting from 1) on successful write, keeping counters on the read and write end in
    sync.

    Args:
        interval (float): interval in seconds between attempts to download a chunk
    """

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
        """Set up a thread to read streaming messages by periodically reading message chunks from a
        target location.

        Args:
            handler (PipesMessageHandler): object to process incoming messages

        Yields:
            PipesParams: A dict of parameters that specifies where a pipes process should write
            pipes protocol message chunks.
        """
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
    def get_params(self) -> Iterator[PipesParams]:
        """Yield a set of parameters to be passed to a message writer in a pipes process.

        Yields:
            PipesParams: A dict of parameters that specifies where a pipes process should write
            pipes protocol message chunks.
        """

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
    "Did you forget to `yield from pipes_session.get_results()` or `return"
    " <PipesClient>.run(...).get_results`? If using `open_pipes_session`,"
    " `pipes_session.get_results` should be called once after the `open_pipes_session` block has"
    " exited to yield any remaining buffered results. If using `<PipesClient>.run`, you should"
    " always return `<PipesClient>.run(...).get_results()`."
)


@experimental
@contextmanager
def open_pipes_session(
    context: OpExecutionContext,
    context_injector: PipesContextInjector,
    message_reader: PipesMessageReader,
    extras: Optional[PipesExtras] = None,
) -> Iterator[PipesSession]:
    """Context manager that opens and closes a pipes session.

    This context manager should be used to wrap the launch of an external process using the pipe
    protocol to report results back to Dagster. The yielded :py:class:`PipesSession` should be used
    to (a) obtain the environment variables that need to be provided to the external process; (b)
    access results streamed back from the external process.

    This method is an alternative to :py:class:`PipesClient` subclasses for users who want more
    control over how pipes processes are launched. When using `open_pipes_session`, it is the user's
    responsibility to inject the message reader and context injector parameters available on the
    yielded `PipesSession` and pass them to the appropriate API when launching the external process.
    Typically these parameters should be set as environment variables.


    Args:
        context (OpExecutionContext): The context for the current op/asset execution.
        context_injector (PipesContextInjector): The context injector to use to inject context into the external process.
        message_reader (PipesMessageReader): The message reader to use to read messages from the external process.
        extras (Optional[PipesExtras]): Optional extras to pass to the external process via the injected context.

    Yields:
        PipesSession: Interface for interacting with the external process.

    .. code-block:: python

        import subprocess
        from dagster import open_pipes_session

        extras = {"foo": "bar"}

        @asset
        def ext_asset(context: OpExecutionContext):
            with open_pipes_session(
                context=context,
                extras={"foo": "bar"},
                context_injector=ExtTempFileContextInjector(),
                message_reader=ExtTempFileMessageReader(),
            ) as pipes_session:
                subprocess.Popen(
                    ["/bin/python", "/path/to/script.py"],
                    env={**pipes_session.get_bootstrap_env_vars()}
                )
                while process.poll() is None:
                    yield from pipes_session.get_results()

            yield from pipes_session.get_results()
    """
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
