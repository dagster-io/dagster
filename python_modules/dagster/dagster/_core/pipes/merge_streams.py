"""Module containing functions for merging log streams."""

import contextlib
import itertools
import logging
import queue
import threading
from collections import deque
from collections.abc import Generator, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, Callable

_default_logger = logging.getLogger(__name__)


@dataclass(frozen=True, order=True)
class LogItem:
    """LogItem to put into the log priority queue."""

    timestamp: str
    log: Any = field(compare=False)


def _deduplicate(recent_messages: "deque[LogItem]") -> Callable[[LogItem], bool]:
    def _should_drop(x: LogItem) -> bool:
        if (
            len(recent_messages) == recent_messages.maxlen
            and x.timestamp <= recent_messages[0].timestamp
        ):
            # We have maxed out the buffer, so drop the messages if we oldest message that we've seen is newer
            # than the message that we are getting from the stream.
            return True

        return x in recent_messages

    return _should_drop


def _enqueue(
    streams: queue.Queue,
    out: queue.PriorityQueue,
    recent_messages_buffer_size: int,
    stream_processor: Callable[[Iterator[bytes]], Iterator[LogItem]],
    logger: logging.Logger,
) -> None:
    """Enqueue all of the log messages to a priority queue.

    This allows us to consume all of the messages in a single thread in case the
    Dagster's handler is not thread safe (which could be the case because right
    now it is being used from a single thread only).

    Args:
    ----
        streams: A queue of all the streams that need to be processed.
        out: The priority queue to output the messages. We use LogItem to output
            it.
        recent_messages_buffer_size: The size of the buffer for storing the recent messages.
        stream_processor: The function that parses the streams into log lines.
        logger: A simple function to print diagnostic logs.

    """
    label, log_stream = streams.get()

    # Fixed length queue to dedupe logs
    recent_messages = deque(maxlen=recent_messages_buffer_size)
    try:
        for i, stream in enumerate(log_stream):
            logger.debug(f"Starting to process the '{label}' log stream: {i}...")
            for log_item in itertools.dropwhile(
                _deduplicate(recent_messages),
                stream_processor(stream),
            ):
                recent_messages.append(log_item)
                out.put(log_item)
    finally:
        logger.debug(f"Finished processing the '{label}' log stream")
        streams.task_done()


def _handle(
    logs: queue.Queue,
    log_handler: Callable,
    shutdown: threading.Event,
    interval: float,
    logger: logging.Logger,
) -> None:
    """Handle all of the logs from the priority queue.

    Args:
    ----
        logs: The logs to process.
        log_handler: The function to call for each log line.
        shutdown: The threading.Event for signaling that we have to stop processing.
        interval: The interval on how often to poll the logs if the queue is empty.
        logger: A simple function to print diagnostic logs.

    """
    logger.debug(
        f"Starting to process the merged log stream, will poll the incoming message queue every {interval}s..."
    )
    while True:
        try:
            # We need to wait for some time for the logs to be put to the priority queue so that they come out as
            # ordered. If we were to wait on the `logs` queue, we would get the log as soon as it is available and that
            # is not what we want.
            entry = logs.get(block=False)
        except queue.Empty:
            shutdown.wait(timeout=interval)
            continue  # we will have special entry in the queue for ending the processing

        try:
            if entry.log is StopIteration:
                logger.debug("Shutting down log handler stream...")
                # This is a special value to finish the processing
                break

            for line in entry.log.split("\n"):
                log_handler(line)
        except Exception as e:
            logger.warning(f"An error occurred during processing '{entry.log}': {e}")
        finally:
            logs.task_done()


@contextlib.contextmanager
def merge_streams(
    streams: Mapping[str, Generator],
    log_handler: Callable,
    stream_processor: Callable[[Iterator[bytes]], Iterator[LogItem]],
    recent_messages_buffer_size: int = 500,
    logger: logging.Logger = _default_logger,
) -> Generator[None, None, None]:
    """merge_streams and handle them with a single handler.

    The list of streams will be processed in separate threads and the handler will accept
    each message separately. We expect streams to produce log messages in the format of
        b'<timestamp> <msg>'

    Args:
    ----
        streams: A dict of generators that will provide log messages. It is expected to sometimes observe duplicate
            messages, which will be deduplicated. The keys to the dictionary are the labels of each stream for
            debugging purposes.
        log_handler: The handler to use on each log message returned
            by the stream.
        stream_processor: The function that parses the streams into log lines.
        recent_messages_buffer_size: The size of the buffer for storing the recent messages.
        logger: The function for logging.

    """
    workers = queue.Queue()
    logs = queue.PriorityQueue()

    for label, log_stream in streams.items():
        workers.put((label, log_stream))

    shutdown = threading.Event()
    threads = [
        # Make threads the individual extract logs calls
        safe_thread(
            target=_enqueue,
            kwargs={
                "streams": workers,
                "out": logs,
                "recent_messages_buffer_size": recent_messages_buffer_size,
                "stream_processor": stream_processor,
                "logger": logger,
            },
            logger=logger,
        )
        for i in range(len(streams))
    ] + [
        # TODO @aignas 2024-03-22: we could add a buffer if there is a lot of lag between
        # when the logs appear in the priority queue and when they are processed.
        safe_thread(
            target=_handle,
            kwargs={
                "logs": logs,
                "log_handler": log_handler,
                "shutdown": shutdown,
                "interval": 1,
                "logger": logger,
            },
            logger=logger,
        ),
    ]

    for t in threads:
        t.start()

    try:
        yield
    finally:
        # The shutdown process is:
        # 1. Wait until all log produces are done
        # 2. Add a special log item that will be processed the last and the handler thread will exit itself
        # 3. Set the shutdown event to signal the thread that it should shutdown.
        # 4. Join the queue
        workers.join()
        logs.put(
            LogItem(
                # Because the timestamps start with a number, any alpha literal will be sorted as the last here
                timestamp="end-of-queue",
                log=StopIteration,
            )
        )
        shutdown.set()
        logs.join()

        # Join the threads to ensure that there are none hanging around
        for t in threads:
            t.join()


def safe_thread(*, target: Callable, logger: logging.Logger, kwargs: dict) -> threading.Thread:
    """Wrap the thread target so that we can capture the exceptions.

    Args:
    ----
        target: The target function.
        logger: A simple function to print diagnostic logs.
        kwargs: The kwargs to pass to the functions that need to be threaded.

    """

    def _fn(**kwargs: Any) -> None:
        try:
            target(**kwargs)
        except Exception as e:
            logger.exception(f"An unhandled exception happened during processing: {e}")

    return threading.Thread(target=_fn, kwargs=kwargs)
