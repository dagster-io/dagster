import builtins
import json
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import IO

import pytest
from dagster._utils import tail_file


def _collect_lines(path: Path, stop_event: threading.Event, out: list[str]) -> None:
    for line in tail_file(str(path), stop_event.is_set):
        out.append(line)


def _run_reader(path: Path, stop_event: threading.Event, out: list[str]) -> threading.Thread:
    thread = threading.Thread(target=_collect_lines, args=(path, stop_event, out))
    thread.start()
    return thread


def _wait_until(predicate: Callable[[], bool], timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


class _ReadlineSpy:
    """File wrapper that records what the reader's readline() calls return."""

    def __init__(self, wrapped: IO[str]) -> None:
        self._wrapped = wrapped
        self.returned: list[str] = []

    def readline(self, *args: object) -> str:
        line = self._wrapped.readline(*args)  # type: ignore[arg-type]
        self.returned.append(line)
        return line

    def __enter__(self) -> "_ReadlineSpy":
        return self

    def __exit__(self, *args: object) -> None:
        self._wrapped.close()


def test_partial_line_held_until_newline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A line written in two chunks must only be yielded once complete.

    Regression test for https://github.com/dagster-io/dagster/issues/34442:
    PipesFileMessageReader json.loads()s every yielded line, so yielding a
    partially written line raised JSONDecodeError and killed the reader thread.
    """
    path = tmp_path / "messages.txt"
    path.touch()

    # Instrument the file object tail_file reads from, so the test knows
    # exactly when the reader has consumed the unfinished fragment instead of
    # guessing with sleeps.
    spies: list[_ReadlineSpy] = []
    real_open = builtins.open

    def spying_open(file: object, *args: object, **kwargs: object) -> object:
        opened = real_open(file, *args, **kwargs)  # type: ignore[arg-type]
        if str(file) == str(path) and (not args or args[0] == "r"):
            spy = _ReadlineSpy(opened)
            spies.append(spy)
            return spy
        return opened

    monkeypatch.setattr(builtins, "open", spying_open)

    stop_event = threading.Event()
    yielded: list[str] = []
    reader = _run_reader(path, stop_event, yielded)
    try:
        assert _wait_until(lambda: len(spies) == 1)
        returned = spies[0].returned

        # Read-progress signal: a complete sentinel line written first must be
        # yielded before anything else is written. Once it arrives, the reader
        # is known to be actively reading at the current file position.
        with real_open(path, "a", encoding="utf-8") as f:
            f.write("sentinel\n")
            f.flush()
        assert _wait_until(lambda: yielded == ["sentinel\n"]), yielded

        # A message line larger than the writer's buffer, written in two
        # chunks, as in the reported failure.
        message = json.dumps({"method": "report", "params": {"key": "x" * 40000}})
        half = len(message) // 2
        fragment = message[:half]
        with real_open(path, "a", encoding="utf-8") as f:
            f.write(fragment)
            f.flush()

        # Wait until the reader's readline() has actually returned the
        # fragment, then until it has polled again. The old implementation
        # yielded the fragment between those two reads, so by the second poll
        # it is guaranteed to have shown up in `yielded` if it ever will.
        assert _wait_until(lambda: fragment in returned), returned[-3:]
        calls_at_fragment = len(returned)
        assert _wait_until(lambda: len(returned) > calls_at_fragment)
        assert yielded == ["sentinel\n"], yielded

        with real_open(path, "a", encoding="utf-8") as f:
            f.write(message[half:] + "\n")
            f.flush()

        # The completed line must arrive before the reader is stopped, not be
        # flushed out by the stop itself.
        assert _wait_until(lambda: yielded == ["sentinel\n", message + "\n"]), yielded
        # The yielded line must parse: this is what the pipes reader does with it.
        assert json.loads(yielded[1])["params"]["key"] == "x" * 40000
    finally:
        stop_event.set()
        reader.join(timeout=5)
    assert not reader.is_alive()


def test_trailing_line_without_newline_still_yielded(tmp_path: Path) -> None:
    """A final line with no trailing newline is still yielded on stop."""
    path = tmp_path / "messages.txt"
    path.write_text("first\nsecond", encoding="utf-8")
    stop_event = threading.Event()
    yielded: list[str] = []
    reader = _run_reader(path, stop_event, yielded)
    try:
        # The complete first line arrives before the stop; only the trailing
        # fragment may wait for it.
        assert _wait_until(lambda: yielded == ["first\n"]), yielded
    finally:
        stop_event.set()
        reader.join(timeout=5)
    assert not reader.is_alive()

    assert yielded == ["first\n", "second"]


def test_complete_lines_pass_through_unchanged(tmp_path: Path) -> None:
    """Complete lines written at once are yielded in order, unchanged."""
    path = tmp_path / "messages.txt"
    path.write_text("one\ntwo\nthree\n", encoding="utf-8")
    stop_event = threading.Event()
    yielded: list[str] = []
    reader = _run_reader(path, stop_event, yielded)
    try:
        assert _wait_until(lambda: yielded == ["one\n", "two\n", "three\n"]), yielded
    finally:
        stop_event.set()
        reader.join(timeout=5)
    assert not reader.is_alive()

    assert yielded == ["one\n", "two\n", "three\n"]
