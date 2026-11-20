import os

import pytest
from dagster._check import CheckError, ParameterCheckError
from dagster._utils import (
    EventGenerationManager,
    ensure_dir,
    ensure_file,
    ensure_gen,
    ensure_single_item,
    touch_file,
)


def test_ensure_single_item():
    assert ensure_single_item({"foo": "bar"}) == ("foo", "bar")
    with pytest.raises(ParameterCheckError, match="Expected dict with single item"):
        ensure_single_item({"foo": "bar", "baz": "quux"})


def test_ensure_gen():
    zero = ensure_gen(0)
    assert next(zero) == 0
    with pytest.raises(StopIteration):
        next(zero)


def test_ensure_dir(tmpdir):
    testdir = os.path.join(str(tmpdir), "test", "dir", "for", "testing", "ensure_dir")
    assert not os.path.exists(testdir)
    ensure_dir(testdir)
    assert os.path.exists(testdir)
    assert os.path.isdir(testdir)
    ensure_dir(testdir)


def test_event_generation_manager():
    def basic_generator():
        yield "A"
        yield "B"
        yield 2
        yield "C"

    with pytest.raises(CheckError, match="Not a generator"):
        EventGenerationManager(None, int)  # ty: ignore[invalid-argument-type]

    with pytest.raises(CheckError, match="must be a class"):
        EventGenerationManager(basic_generator(), None)  # ty: ignore[invalid-argument-type]

    with pytest.raises(CheckError, match="Called `get_object` before `generate_setup_events`"):
        basic_manager = EventGenerationManager(basic_generator(), int)
        basic_manager.get_object()

    with pytest.raises(CheckError, match="generator never yielded object of type bool"):
        basic_manager = EventGenerationManager(basic_generator(), bool)
        list(basic_manager.generate_setup_events())
        basic_manager.get_object()

    basic_manager = EventGenerationManager(basic_generator(), int)
    setup_events = list(basic_manager.generate_setup_events())
    assert setup_events == ["A", "B"]
    result = basic_manager.get_object()
    assert result == 2
    teardown_events = list(basic_manager.generate_teardown_events())
    assert teardown_events == ["C"]


@pytest.mark.parametrize("create_file", [ensure_file, touch_file])
def test_file_helpers_accept_relative_basename(tmp_path, monkeypatch, create_file):
    monkeypatch.chdir(tmp_path)
    create_file("output.txt")
    assert (tmp_path / "output.txt").is_file()
    (tmp_path / "output.txt").write_text("preserved", encoding="utf-8")
    create_file("output.txt")
    assert (tmp_path / "output.txt").read_text(encoding="utf-8") == "preserved"
