import os

import pytest
from dagster.check import CheckError, ParameterCheckError
from dagster.utils import EventGenerationManager, ensure_dir, ensure_gen, ensure_single_item


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
        EventGenerationManager(None, int)

    with pytest.raises(CheckError, match="was supposed to be a type"):
        EventGenerationManager(basic_generator(), None)

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
