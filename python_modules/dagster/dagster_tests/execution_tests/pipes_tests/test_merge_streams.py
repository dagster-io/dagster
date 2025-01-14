import itertools
import textwrap
from collections.abc import Iterator
from datetime import datetime
from queue import Queue

import pytest
from dagster._core.pipes.merge_streams import LogItem, merge_streams


# Example stream processor that follows Kubernetes log format
# Borrowed from dagster-k8s/dagster_k8s/pipes.py
def _process_log_stream(stream: Iterator[bytes]) -> Iterator[LogItem]:
    timestamp = ""
    log = ""

    for log_chunk in stream:
        for line in log_chunk.decode("utf-8").split("\n"):
            maybe_timestamp, _, tail = line.partition(" ")
            if not timestamp:
                # The first item in the stream will always have a timestamp.
                timestamp = maybe_timestamp
                log = tail
            elif maybe_timestamp == timestamp:
                # We have multiple messages with the same timestamp in this chunk, add them separated
                # with a new line
                log += f"\n{tail}"
            elif not (len(maybe_timestamp) == len(timestamp) and _is_timestamp(maybe_timestamp)):
                # The line is continuation of a long line that got truncated and thus doesn't
                # have a timestamp in the beginning of the line.
                # Since all timestamps in the RFC format returned by Kubernetes have the same
                # length (when represented as strings) we know that the value won't be a timestamp
                # if the string lengths differ, however if they do not differ, we need to parse the
                # timestamp.
                log += line
            else:
                # New log line has been observed, send in the next cycle
                yield LogItem(timestamp=timestamp, log=log)
                timestamp = maybe_timestamp
                log = tail

    # Send the last message that we were building
    if log or timestamp:
        yield LogItem(timestamp=timestamp, log=log)


def _is_timestamp(maybe_timestamp: str) -> bool:
    # fromisoformat only works properly in Python 3.11+
    # Once pre 3.11 backwards compatibility is dropped
    # we can use that instead
    try:
        datetime.strptime(maybe_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        return True
    except ValueError:
        return False


def _iter_all(q):
    while True:
        item = q.get(block=True)
        if item is StopIteration:
            break

        yield item


def _iter(q):
    gen = _iter_all(q)
    item = None
    while True:
        chunk = [item] if item is not None else []
        chunk.extend(itertools.takewhile(lambda x: x is not None, gen))
        yield chunk

        try:
            # Attempt to consume from the
            # https://docs.python.org/3/library/itertools.html#itertools.takewhile
            item = next(gen)
        except StopIteration:
            break


def _replay(*, producers, events):
    for event in events:
        producer_id, event = event  # noqa: PLW2901
        producers[producer_id].put(event)

    for p in producers.values():
        p.put(StopIteration)


def _test_merge_logs(*events, recent_messages_buffer_size=10):
    producers = {i[0]: Queue() for i in events if i}
    out = []

    def handler(x):
        out.append(x)

    with merge_streams(
        streams={str(key): _iter(p) for key, p in producers.items()},
        log_handler=handler,
        stream_processor=_process_log_stream,
        recent_messages_buffer_size=recent_messages_buffer_size,
    ):
        _replay(producers=producers, events=events)

    return out


def test_empty_stream():
    got = _test_merge_logs((0, None))

    assert [] == got


def test_single_stream():
    got = _test_merge_logs(
        (0, b'2024-03-22T02:17:29.1855Z {"order": "1"}'),
        (0, b'2024-03-22T02:17:29.2855Z {"order": "2"}'),
        (0, b'2024-03-22T02:17:29.3855Z {"order": "3"}'),
    )

    assert [
        '{"order": "1"}',
        '{"order": "2"}',
        '{"order": "3"}',
    ] == got


def test_single_stream_out_of_order():
    got = _test_merge_logs(
        (0, b'2024-03-22T02:17:29.1855Z {"order": "1"}'),
        (0, b'2024-03-22T02:17:29.3855Z {"order": "3"}'),
        (0, b'2024-03-22T02:17:29.2855Z {"order": "2"}'),
    )

    assert [
        '{"order": "1"}',
        '{"order": "2"}',
        '{"order": "3"}',
    ] == got


def test_three_containers_simple():
    got = _test_merge_logs(
        (0, b'2024-03-22T02:17:29.1855Z {"order": "1"}'),
        (1, b'2024-03-22T02:17:29.2855Z {"order": "2"}'),
        (2, b'2024-03-22T02:17:29.3855Z {"order": "3"}'),
        (0, b'2024-03-22T02:17:29.4855Z {"order": "4"}'),
        (1, b'2024-03-22T02:17:29.5855Z {"order": "5"}'),
        (2, b'2024-03-22T02:17:29.6855Z {"order": "6"}'),
        (0, b'2024-03-22T02:17:29.7855Z {"order": "7"}'),
        (1, b'2024-03-22T02:17:29.8855Z {"order": "8"}'),
        (2, b'2024-03-22T02:17:29.9855Z {"order": "9"}'),
    )

    assert [f'{{"order": "{i}"}}' for i in range(1, 10)] == got


def test_multi_stream_different_volumes():
    got = _test_merge_logs(
        (0, b"2024-03-22T02:17:29.1855Z Downloading files"),
        (0, b"2024-03-22T02:17:29.2855Z Still downloading"),
        (0, b"2024-03-22T02:17:29.3855Z Finished downloading"),
        (1, b"2024-03-22T02:17:29.4855Z Main booting"),
        (2, b"2024-03-22T02:17:29.5855Z Sidecar booting"),
        (1, b"2024-03-22T02:17:29.6855Z Main started"),
        (1, b"2024-03-22T02:17:29.7855Z Main finished"),
        (2, b"2024-03-22T02:17:29.8855Z Sidecar waiting"),
        (2, b"2024-03-22T02:17:29.9855Z Sidecar finished"),
    )

    assert [
        "Downloading files",
        "Still downloading",
        "Finished downloading",
        "Main booting",
        "Sidecar booting",
        "Main started",
        "Main finished",
        "Sidecar waiting",
        "Sidecar finished",
    ] == got


def test_multi_line_interleaved():
    got = _test_merge_logs(
        (
            0,
            textwrap.dedent(
                """\
                2024-03-22T02:17:29.1855Z Downloading files
                2024-03-22T02:17:29.2855Z Still downloading
                2024-03-22T02:17:29.3855Z Finished downloading"""
            ).encode("utf-8"),
        ),
        (
            1,
            textwrap.dedent(
                """\
                2024-03-22T02:17:29.4855Z Main booting
                2024-03-22T02:17:29.6855Z Main started"""
            ).encode("utf-8"),
        ),
        (2, b"2024-03-22T02:17:29.5855Z Sidecar booting"),
        (1, b"2024-03-22T02:17:29.7855Z Main finished"),
        (2, b"2024-03-22T02:17:29.8855Z Sidecar waiting"),
        (2, b"2024-03-22T02:17:29.9855Z Sidecar finished"),
    )

    assert [
        "Downloading files",
        "Still downloading",
        "Finished downloading",
        "Main booting",
        "Sidecar booting",
        "Main started",
        "Main finished",
        "Sidecar waiting",
        "Sidecar finished",
    ] == got


def test_deduplicating_logs():
    got = _test_merge_logs(
        (
            0,
            textwrap.dedent(
                """\
                2024-03-22T02:17:29.1855Z Downloading files
                2024-03-22T02:17:29.2855Z Still downloading
                2024-03-22T02:17:29.3855Z Finished downloading"""
            ).encode("utf-8"),
        ),
        (
            1,
            textwrap.dedent(
                """\
                2024-03-22T02:17:29.4855Z Main booting
                2024-03-22T02:17:29.6855Z Main started"""
            ).encode("utf-8"),
        ),
        (2, b"2024-03-22T02:17:29.5855Z Sidecar booting"),
        (1, None),
        (
            1,
            textwrap.dedent(
                """\
                2024-03-22T02:17:29.4855Z Main booting
                2024-03-22T02:17:29.6855Z Main started
                2024-03-22T02:17:29.7855Z Main finished with a restart"""
            ).encode("utf-8"),
        ),
        (2, b"2024-03-22T02:17:29.8855Z Sidecar waiting"),
        # Simulate a crash with a duplicate log line
        (2, None),
        (2, b"2024-03-22T02:17:29.8855Z Sidecar waiting"),
        # Simulate a few restarts in a row with a final message from the sidecar
        (2, None),
        (2, None),
        (2, b"2024-03-22T02:17:29.9855Z Sidecar finished"),
    )

    assert [
        "Downloading files",
        "Still downloading",
        "Finished downloading",
        "Main booting",
        "Sidecar booting",
        "Main started",
        "Main finished with a restart",
        "Sidecar waiting",
        "Sidecar finished",
    ] == got


def test_deduplicating_logs_with_buffer():
    got = _test_merge_logs(
        (0, b"2024-03-22T02:17:29.9855Z First message"),
        (0, b"2024-03-22T02:17:29.9855Z Second message"),
        (0, b"2024-03-22T02:17:29.9855Z Third message"),
        (0, None),
        (0, b"2024-03-22T02:17:29.9855Z First message"),
        (0, b"2024-03-22T02:17:29.9855Z Second message"),
        (0, b"2024-03-22T02:17:29.9855Z Third message"),
        recent_messages_buffer_size=1,
    )

    assert [
        "First message",
        "Second message",
        "Third message",
    ] == got


def test_exception_inside_context_manager():
    producers = {i: Queue() for i in range(10)}
    out = []

    def handler(x):
        out.append(x)

    for p in producers.values():
        p.put(b"Hello!")
        p.put(StopIteration)

    def _fn():
        with merge_streams(
            streams={str(key): _iter(p) for key, p in producers.items()},
            log_handler=handler,
            stream_processor=_process_log_stream,
        ):
            raise RuntimeError("error during merging streams")

    with pytest.raises(RuntimeError) as exc_info:
        _fn()

    assert exc_info.value.args == ("error during merging streams",)


def test_exception_inside_producer(caplog):
    producers = {i: Queue() for i in range(3)}

    for p in producers.values():
        p.put(b"Hello!")
        p.put("Passing a string will throw an error in the thread that does decoding and de-duping")
        p.put(StopIteration)
    out = []

    def handler(x):
        out.append(x)

    with merge_streams(
        streams={str(key): _iter(p) for key, p in producers.items()},
        log_handler=handler,
        stream_processor=_process_log_stream,
    ):
        pass

    assert "has no attribute 'decode'" in caplog.text


def test_exception_inside_consumer(caplog):
    producers = {i: Queue() for i in range(3)}

    for p in producers.values():
        p.put(b"Hello!")
        p.put(StopIteration)

    def handler(x):
        raise ValueError(f"error in a handler: {x}")

    with merge_streams(
        streams={str(key): _iter(p) for key, p in producers.items()},
        log_handler=handler,
        stream_processor=_process_log_stream,
    ):
        pass

    assert "error in a handler" in caplog.text


def test_multiple_lines_in_a_chunk_with_the_same_timestamp():
    got = _test_merge_logs(
        (
            0,
            textwrap.dedent(
                """\
                2024-03-22T02:17:29.4855Z {"order": "1"}
                2024-03-22T02:17:29.4855Z {"order": "2"}
                2024-03-22T02:17:29.4855Z {"order": "3"}
                """
            ).encode("utf-8"),
        ),
    )

    assert [
        '{"order": "1"}',
        '{"order": "2"}',
        '{"order": "3"}',
    ] == got


def test_multiple_lines_in_a_chunk_with_lines_without_timestamp():
    got = _test_merge_logs(
        (
            0,
            textwrap.dedent(
                """\
                2024-03-22T02:17:29.4855Z {"order":
                 "1"}
                2024-03-22T02:17:29.4855Z {"order":
                 "2"}
                2024-03-22T02:17:29.4855Z {"order":
                """
            ).encode("utf-8"),
        ),
        (
            0,
            textwrap.dedent(
                """\
                 "3"}
                2024-03-22T02:17:29.4855Z {"order": "4",
                 "more_content_fill_to_eq_ts": "extra"}
                """
            ).encode("utf-8"),
        ),
    )

    assert [
        '{"order": "1"}',
        '{"order": "2"}',
        '{"order": "3"}',
        '{"order": "4", "more_content_fill_to_eq_ts": "extra"}',
    ] == got
