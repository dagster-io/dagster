import datetime
import json
import os
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from threading import Event, Thread
from typing import Iterator, Optional, TextIO

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

    def no_messages_debug_text(self) -> str:
        return f"Attempted to inject context via file {self._path}"


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

    def no_messages_debug_text(self) -> str:
        return "Attempted to inject context via a temporary file."


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

    def no_messages_debug_text(self) -> str:
        return "Attempted to inject context directly, typically as an environment variable."


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
        """Set up a thread to read streaming messages from the external process by tailing the
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

    def no_messages_debug_text(self) -> str:
        return f"Attempted to read messages from file {self._path}."


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

    def no_messages_debug_text(self) -> str:
        return "Attempted to read messages from a local temporary file."


# Number of seconds to wait after an external process has completed for stdio logs to become
# available. If this is exceeded, proceed with exiting without picking up logs.
WAIT_FOR_STDIO_LOGS_TIMEOUT = 60


@experimental
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

    If `stdout_reader` or `stderr_reader` are passed, this reader will also start them when
    `read_messages` is called. If they are not passed, then the reader performs no stdout/stderr
    forwarding.

    Args:
        interval (float): interval in seconds between attempts to download a chunk
        stdout_reader (Optional[PipesBlobStoreStdioReader]): A reader for reading stdout logs.
        stderr_reader (Optional[PipesBlobStoreStdioReader]): A reader for reading stderr logs.
    """

    interval: float
    counter: int
    stdout_reader: "PipesBlobStoreStdioReader"
    stderr_reader: "PipesBlobStoreStdioReader"

    def __init__(
        self,
        interval: float = 10,
        stdout_reader: Optional["PipesBlobStoreStdioReader"] = None,
        stderr_reader: Optional["PipesBlobStoreStdioReader"] = None,
    ):
        self.interval = interval
        self.counter = 1
        self.stdout_reader = (
            check.opt_inst_param(stdout_reader, "stdout_reader", PipesBlobStoreStdioReader)
            or PipesNoOpStdioReader()
        )
        self.stderr_reader = (
            check.opt_inst_param(stderr_reader, "stderr_reader", PipesBlobStoreStdioReader)
            or PipesNoOpStdioReader()
        )

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
            messages_thread = None
            try:
                messages_thread = Thread(
                    target=self._messages_thread, args=(handler, params, is_task_complete)
                )
                messages_thread.start()
                self.stdout_reader.start(params, is_task_complete)
                self.stderr_reader.start(params, is_task_complete)
                yield params
            finally:
                self.wait_for_stdio_logs(params)
                is_task_complete.set()
                if messages_thread:
                    messages_thread.join()
                self.stdout_reader.stop()
                self.stderr_reader.stop()

    # In cases where we are forwarding logs, in some cases the logs might not be written out until
    # after the run completes. We wait for them to exist.
    def wait_for_stdio_logs(self, params):
        start_or_last_download = datetime.datetime.now()
        while (
            datetime.datetime.now() - start_or_last_download
        ).seconds <= WAIT_FOR_STDIO_LOGS_TIMEOUT and (
            (self.stdout_reader and not self.stdout_reader.is_ready(params))
            or (self.stderr_reader and not self.stderr_reader.is_ready(params))
        ):
            time.sleep(5)

    @abstractmethod
    @contextmanager
    def get_params(self) -> Iterator[PipesParams]:
        """Yield a set of parameters to be passed to a message writer in a pipes process.

        Yields:
            PipesParams: A dict of parameters that specifies where a pipes process should write
            pipes protocol message chunks.
        """

    @abstractmethod
    def download_messages_chunk(self, index: int, params: PipesParams) -> Optional[str]:
        ...

    def _messages_thread(
        self,
        handler: "PipesMessageHandler",
        params: PipesParams,
        is_task_complete: Event,
    ) -> None:
        start_or_last_download = datetime.datetime.now()
        while True:
            now = datetime.datetime.now()
            if (now - start_or_last_download).seconds > self.interval or is_task_complete.is_set():
                start_or_last_download = now
                chunk = self.download_messages_chunk(self.counter, params)
                if chunk:
                    for line in chunk.split("\n"):
                        message = json.loads(line)
                        handler.handle_message(message)
                    self.counter += 1
                elif is_task_complete.is_set():
                    break
            time.sleep(1)


class PipesBlobStoreStdioReader(ABC):
    @abstractmethod
    def start(self, params: PipesParams, is_task_complete: Event) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...

    @abstractmethod
    def is_ready(self, params: PipesParams) -> bool:
        ...


@experimental
class PipesChunkedStdioReader(PipesBlobStoreStdioReader):
    """Reader for reading stdout/stderr logs from a blob store such as S3, Azure blob storage, or GCS.

    Args:
        interval (float): interval in seconds between attempts to download a chunk.
        target_stream (TextIO): The stream to which to write the logs. Typcially `sys.stdout` or `sys.stderr`.
    """

    def __init__(self, *, interval: float = 10, target_stream: TextIO):
        self.interval = interval
        self.target_stream = target_stream
        self.thread: Optional[Thread] = None

    @abstractmethod
    def download_log_chunk(self, params: PipesParams) -> Optional[str]:
        ...

    def start(self, params: PipesParams, is_task_complete: Event) -> None:
        self.thread = Thread(target=self._reader_thread, args=(params, is_task_complete))
        self.thread.start()

    def stop(self) -> None:
        if self.thread:
            self.thread.join()

    def _reader_thread(
        self,
        params: PipesParams,
        is_task_complete: Event,
    ) -> None:
        start_or_last_download = datetime.datetime.now()
        while True:
            now = datetime.datetime.now()
            if (
                (now - start_or_last_download).seconds > self.interval or is_task_complete.is_set()
            ) and self.is_ready(params):
                start_or_last_download = now
                chunk = self.download_log_chunk(params)
                if chunk:
                    self.target_stream.write(chunk)
                elif is_task_complete.is_set():
                    break
            time.sleep(self.interval)


class PipesNoOpStdioReader(PipesBlobStoreStdioReader):
    """Default implementation for a pipes stdio reader that does nothing."""

    def start(self, params: PipesParams, is_task_complete: Event) -> None:
        pass

    def stop(self) -> None:
        pass

    def is_ready(self, params: PipesParams) -> bool:
        return True


def extract_message_or_forward_to_stdout(handler: "PipesMessageHandler", log_line: str):
    # exceptions as control flow, you love to see it
    try:
        message = json.loads(log_line)
        if PIPES_PROTOCOL_VERSION_FIELD in message.keys():
            handler.handle_message(message)
        else:
            sys.stdout.writelines((log_line, "\n"))
    except Exception:
        # move non-message logs in to stdout for compute log capture
        sys.stdout.writelines((log_line, "\n"))


_FAIL_TO_YIELD_ERROR_MESSAGE = (
    "Did you forget to `yield from pipes_session.get_results()` or `return"
    " <PipesClient>.run(...).get_results`? If using `open_pipes_session`,"
    " `pipes_session.get_results` should be called once after the `open_pipes_session` block has"
    " exited to yield any remaining buffered results via `<PipesSession>.get_results()`."
    " If using `<PipesClient>.run`, you should always return"
    " `<PipesClient>.run(...).get_results()` or `<PipesClient>.run(...).get_materialize_result()`."
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
    try:
        with context_injector.inject_context(
            context_data
        ) as ci_params, message_handler.handle_messages(message_reader) as mr_params:
            yield PipesSession(
                context_data=context_data,
                message_handler=message_handler,
                context_injector_params=ci_params,
                message_reader_params=mr_params,
            )
    finally:
        if not message_handler.received_any_message:
            context.log.warn(
                "[pipes] did not receive any messages from external process. Check stdout / stderr"
                " logs from the external process if"
                f" possible.\n{context_injector.__class__.__name__}:"
                f" {context_injector.no_messages_debug_text()}\n{message_reader.__class__.__name__}:"
                f" {message_reader.no_messages_debug_text()}\n"
            )
        elif not message_handler.received_closed_message:
            context.log.warn(
                "[pipes] did not receive closed message from external process. Buffered messages"
                " may have been discarded without being delivered. Use `open_dagster_pipes` as a"
                " context manager (a with block) to ensure that cleanup is successfully completed."
                " If that is not possible, manually call `PipesContext.close()` before process"
                " exit."
            )
