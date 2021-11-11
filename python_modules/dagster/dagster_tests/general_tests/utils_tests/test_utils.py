import os

import pytest
from dagster.check import CheckError, ParameterCheckError
from dagster.utils import (
    EventGenerationManager,
    LRUCache,
    ensure_dir,
    ensure_gen,
    ensure_single_item,
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


def test_lru_cache():
    cache = LRUCache(capacity=2)

    assert not cache.has("one")
    assert not cache.has("two")
    assert not cache.has("three")

    cache.put("one", 1)
    assert cache.has("one")
    assert cache.get("one") == 1
    assert not cache.has("two")
    assert not cache.has("three")

    cache.put("two", 2)
    assert cache.has("one")
    assert cache.get("one") == 1
    assert cache.has("two")
    assert cache.get("two") == 2
    assert not cache.has("three")

    # test rotation
    cache.put("three", 3)
    assert not cache.has("one")
    assert cache.get("one") == None
    assert cache.has("two")
    assert cache.get("two") == 2
    assert cache.has("three")
    assert cache.get("three") == 3

    # test clear
    cache.clear("three")
    assert not cache.has("one")
    assert cache.has("two")
    assert not cache.has("three")

    # test clear all
    cache.clear_all()
    assert not cache.has("one")
    assert not cache.has("two")
    assert not cache.has("three")
