import json
import threading
import time
from pathlib import Path

from dagster._utils import tail_file


def _collect_lines(path: Path, stop_event: threading.Event, out: list[str]) -> None:
    for line in tail_file(str(path), stop_event.is_set):
        out.append(line)


def _run_reader(path: Path, stop_event: threading.Event, out: list[str]) -> threading.Thread:
    thread = threading.Thread(target=_collect_lines, args=(path, stop_event, out))
    thread.start()
    return thread


def test_partial_line_held_until_newline(tmp_path: Path) -> None:
    """A line written in two chunks must only be yielded once complete.

    Regression test for https://github.com/dagster-io/dagster/issues/34442:
    PipesFileMessageReader json.loads()s every yielded line, so yielding a
    partially written line raised JSONDecodeError and killed the reader thread.
    """
    path = tmp_path / "messages.txt"
    path.touch()
    stop_event = threading.Event()
    yielded: list[str] = []
    reader = _run_reader(path, stop_event, yielded)

    # A message line larger than the writer's buffer, written in two chunks
    # with a pause in between, as in the reported failure.
    message = json.dumps({"method": "report", "params": {"key": "x" * 40000}})
    half = len(message) // 2
    with open(path, "a", encoding="utf-8") as f:
        f.write(message[:half])
        f.flush()
        time.sleep(0.3)
        f.write(message[half:] + "\n")
        f.flush()

    time.sleep(0.2)
    stop_event.set()
    reader.join(timeout=5)
    assert not reader.is_alive()

    assert yielded == [message + "\n"]
    # The yielded line must parse: this is what the pipes reader does with it.
    assert json.loads(yielded[0])["params"]["key"] == "x" * 40000


def test_trailing_line_without_newline_still_yielded(tmp_path: Path) -> None:
    """A final line with no trailing newline is still yielded on stop."""
    path = tmp_path / "messages.txt"
    path.write_text("first\nsecond", encoding="utf-8")
    stop_event = threading.Event()
    yielded: list[str] = []
    reader = _run_reader(path, stop_event, yielded)

    time.sleep(0.3)
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

    time.sleep(0.3)
    stop_event.set()
    reader.join(timeout=5)
    assert not reader.is_alive()

    assert yielded == ["one\n", "two\n", "three\n"]
