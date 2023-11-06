import datetime
import json
import os
import sys
import tempfile
import time
import warnings
from abc import ABC, abstractmethod
from contextlib import contextmanager
from threading import Event, Thread
from typing import Iterator, Optional, Sequence, TextIO

from dagster_pipes import (
    PIPES_PROTOCOL_VERSION_FIELD,
    PipesContextData,
    PipesDefaultContextLoader,
    PipesDefaultMessageWriter,
    PipesExtras,
    PipesOpenedData,
    PipesParams,
)

from dagster import (
    OpExecutionContext,
    _check as check,
)
from dagster._annotations import experimental
from dagster._core.errors import DagsterInvariantViolationError, DagsterPipesExecutionError
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
        is_session_closed = Event()
        thread = None
        try:
            open(self._path, "w").close()  # create file
            thread = Thread(
                target=self._reader_thread, args=(handler, is_session_closed), daemon=True
            )
            thread.start()
            yield {PipesDefaultMessageWriter.FILE_PATH_KEY: self._path}
        finally:
            is_session_closed.set()
            if os.path.exists(self._path):
                os.remove(self._path)
            if thread:
                thread.join()

    def _reader_thread(self, handler: "PipesMessageHandler", is_resource_complete: Event) -> None:
        try:
            for line in tail_file(self._path, lambda: is_resource_complete.is_set()):
                message = json.loads(line)
                handler.handle_message(message)
        except:
            handler.report_pipes_framework_exception(
                f"{self.__class__.__name__} reader thread",
                sys.exc_info(),
            )
            raise

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


# Time in seconds to wait between attempts when polling for some condition. Default value that is
# used in several places.
DEFAULT_SLEEP_INTERVAL = 1

# Wait up to this many seconds for threads to finish executing during cleanup. Note that this must
# be longer than WAIT_FOR_LOGS_TIMEOUT.
THREAD_WAIT_TIMEOUT = 120

# Buffer period after the external process has completed before we attempt to close out the log
# thread. The purpose of this is to allow an external system to update logs to their final state,
# which may take some time after the external process has completed. This is subtly different than
# `WAIT_FOR_LOGS_TIMEOUT`, which is the amount of time we will wait for targeted log files to exist
# at all. In contrast, `WAIT_FOR_LOGS_AFTER_EXECUTION_SECONDS` is used to guard against the case
# where log files exist but incomplete immediately after the external process has completed.
WAIT_FOR_LOGS_AFTER_EXECUTION_INTERVAL = 10

# Number of seconds to wait after an external process has completed to close
# out the log thread. This is necessary because the log thread contains two
# points at which it waits indefinitely: (1) for the `opened` message to be
# received; (2) for the log files to exist (which may not occur until some time
# after the external process has completed).
WAIT_FOR_LOGS_TIMEOUT = 60


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

    If `log_readers` is passed, the message reader will start the passed log readers when the
    `opened` message is received from the external process.

    Args:
        interval (float): interval in seconds between attempts to download a chunk
        log_readers (Optional[Sequence[PipesLogReader]]): A set of readers for logs.
    """

    interval: float
    counter: int
    log_readers: Sequence["PipesLogReader"]
    opened_payload: Optional[PipesOpenedData]

    def __init__(
        self,
        interval: float = 10,
        log_readers: Optional[Sequence["PipesLogReader"]] = None,
    ):
        self.interval = interval
        self.counter = 1
        self.log_readers = check.opt_sequence_param(
            log_readers, "log_readers", of_type=PipesLogReader
        )
        self.opened_payload = None

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
            is_session_closed = Event()
            messages_thread = None
            logs_thread = None
            try:
                messages_thread = Thread(
                    target=self._messages_thread,
                    args=(handler, params, is_session_closed),
                    daemon=True,
                )
                messages_thread.start()
                logs_thread = Thread(
                    target=self._logs_thread,
                    args=(handler, params, is_session_closed, messages_thread),
                    daemon=True,
                )
                logs_thread.start()
                yield params
            finally:
                is_session_closed.set()
                if messages_thread:
                    _join_thread(messages_thread, "messages")
                if logs_thread:
                    _join_thread(logs_thread, "logs")

    def on_opened(self, opened_payload: PipesOpenedData) -> None:
        self.opened_payload = opened_payload

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
        is_session_closed: Event,
    ) -> None:
        try:
            start_or_last_download = datetime.datetime.now()
            while True:
                now = datetime.datetime.now()
                if (
                    now - start_or_last_download
                ).seconds > self.interval or is_session_closed.is_set():
                    start_or_last_download = now
                    chunk = self.download_messages_chunk(self.counter, params)
                    if chunk:
                        for line in chunk.split("\n"):
                            message = json.loads(line)
                            handler.handle_message(message)
                        self.counter += 1
                    elif is_session_closed.is_set():
                        break
                time.sleep(DEFAULT_SLEEP_INTERVAL)
        except:
            handler.report_pipes_framework_exception(
                f"{self.__class__.__name__} messages thread",
                sys.exc_info(),
            )
            raise

    def _logs_thread(
        self,
        handler: "PipesMessageHandler",
        params: PipesParams,
        is_session_closed: Event,
        messages_thread: Thread,
    ) -> None:
        # Start once we have received the opened message from the external process
        while True:
            if self.opened_payload is not None:
                break
            # We never received the `opened` message and never will, so don't try to start the log
            # reader threads.
            elif not messages_thread.is_alive():
                return
            time.sleep(DEFAULT_SLEEP_INTERVAL)

        # Logs are started with a merge of the params generated by the message reader and the opened
        # payload.
        log_params = {**params, **self.opened_payload}

        # Loop over all log readers and start them if the target is readable, which typically means
        # a file exists at the target location. Different execution environments may write logs at
        # different times (e.g., some may write logs periodically during execution, while others may
        # only write logs after the process has completed).
        try:
            unstarted_log_readers = list(self.log_readers)
            wait_for_logs_start = None
            while unstarted_log_readers:
                # iterate in reverse so we can pop off elements as we go
                for i in reversed(range(len(unstarted_log_readers))):
                    if unstarted_log_readers[i].target_is_readable(log_params):
                        reader = unstarted_log_readers.pop(i)
                        reader.start(log_params, is_session_closed)

                # In some cases logs might not be written out until after the external process has
                # exited. That will leave us in this state, where some log readers have not been
                # started even though the external process is finished. We start a timer and wait
                # for up to WAIT_FOR_LOGS_TIMEOUT seconds for the logs to be written. If they are
                # not written after this amount of time has elapsed, we warn the user and bail.
                if is_session_closed.is_set():
                    if wait_for_logs_start is None:
                        wait_for_logs_start = datetime.datetime.now()
                    if (
                        datetime.datetime.now() - wait_for_logs_start
                    ).seconds > WAIT_FOR_LOGS_TIMEOUT:
                        for log_reader in unstarted_log_readers:
                            warnings.warn(
                                f"Attempted to read log for reader {log_reader.name} but log was"
                                " still not written {WAIT_FOR_LOGS_TIMEOUT} seconds after session close. Abandoning log."
                            )
                        break
                time.sleep(DEFAULT_SLEEP_INTERVAL)

            # Wait for the external process to complete
            is_session_closed.wait()
        except:
            handler.report_pipes_framework_exception(
                f"{self.__class__.__name__} logs thread",
                sys.exc_info(),
            )
            raise
        finally:
            for log_reader in self.log_readers:
                if log_reader.is_running():
                    log_reader.stop()


class PipesLogReader(ABC):
    @abstractmethod
    def start(self, params: PipesParams, is_session_closed: Event) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...

    @abstractmethod
    def is_running(self) -> bool:
        ...

    @abstractmethod
    def target_is_readable(self, params: PipesParams) -> bool:
        ...

    @property
    def name(self) -> str:
        """Override this to distinguish different log readers in error messages."""
        return self.__class__.__name__


@experimental
class PipesChunkedLogReader(PipesLogReader):
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

    def start(self, params: PipesParams, is_session_closed: Event) -> None:
        self.thread = Thread(target=self._reader_thread, args=(params, is_session_closed))
        self.thread.start()

    def stop(self) -> None:
        if self.thread is None:
            raise DagsterInvariantViolationError(
                "Attempted to wait for log reader to finish, but it was never started."
            )
        _join_thread(self.thread, self.name)

    def is_running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def _reader_thread(
        self,
        params: PipesParams,
        is_session_closed: Event,
    ) -> None:
        start_or_last_download = datetime.datetime.now()
        after_execution_time_start = None
        while True:
            now = datetime.datetime.now()
            if (now - start_or_last_download).seconds > self.interval or is_session_closed.is_set():
                start_or_last_download = now
                chunk = self.download_log_chunk(params)
                if chunk:
                    self.target_stream.write(chunk)

                # After execution is complete, we don't want to immediately exit, because it is
                # possible the external system will take some time to flush logs to the external
                # storage system. Only exit after WAIT_FOR_LOGS_AFTER_EXECUTION_INTERVAL seconds
                # have elapsed.
                elif is_session_closed.is_set():
                    if after_execution_time_start is None:
                        after_execution_time_start = datetime.datetime.now()
                    elif (
                        datetime.datetime.now() - after_execution_time_start
                    ).seconds > WAIT_FOR_LOGS_AFTER_EXECUTION_INTERVAL:
                        break
                time.sleep(self.interval)


def _join_thread(thread: Thread, thread_name: str) -> None:
    thread.join(timeout=THREAD_WAIT_TIMEOUT)
    if thread.is_alive():
        raise DagsterPipesExecutionError(f"Timed out waiting for {thread_name} thread to finish.")


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
    message_handler = PipesMessageHandler(context, message_reader)
    try:
        with context_injector.inject_context(
            context_data
        ) as ci_params, message_handler.handle_messages() as mr_params:
            yield PipesSession(
                context_data=context_data,
                message_handler=message_handler,
                context_injector_params=ci_params,
                message_reader_params=mr_params,
            )
    finally:
        if not message_handler.received_opened_message:
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
