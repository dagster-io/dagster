import pytest
from dagster.check import CheckError
from dagster.core.definitions.dependency import SolidHandle
from dagster.seven import json


def test_handle_path():
    handle = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", None)))
    assert handle.path == ["foo", "bar", "baz"]
    assert SolidHandle.from_path(handle.path) == handle

    handle = SolidHandle("foo", None)
    assert handle.path == ["foo"]
    assert SolidHandle.from_path(handle.path) == handle


def test_handle_to_from_string():
    handle = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", None)))
    assert handle.to_string() == "foo.bar.baz"
    assert SolidHandle.from_string(handle.to_string()) == handle

    handle = SolidHandle("foo", None)
    assert handle.to_string() == "foo"
    assert SolidHandle.from_string(handle.to_string()) == handle


def test_is_or_descends_from():
    ancestor = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", SolidHandle("quux", None))))
    descendant = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", None)))
    assert not descendant.is_or_descends_from(ancestor)

    ancestor = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", None)))
    descendant = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", None)))
    assert descendant.is_or_descends_from(ancestor)

    ancestor = SolidHandle("bar", SolidHandle("foo", None))
    descendant = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", None)))
    assert descendant.is_or_descends_from(ancestor)

    ancestor = SolidHandle("foo", None)
    descendant = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", None)))
    assert descendant.is_or_descends_from(ancestor)

    ancestor = SolidHandle("foo", None)
    descendant = SolidHandle("foo", None)
    assert descendant.is_or_descends_from(ancestor)

    ancestor = SolidHandle("foo", None)
    descendant = SolidHandle("bar", None)
    assert not descendant.is_or_descends_from(ancestor)

    ancestor = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", None)))
    descendant = SolidHandle("baz", None)
    assert not descendant.is_or_descends_from(ancestor)

    ancestor = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", None)))
    descendant = SolidHandle("baz", SolidHandle("bar", None))
    assert not descendant.is_or_descends_from(ancestor)


def test_pop():
    handle = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", None)))
    assert handle.pop(SolidHandle("foo", None)) == SolidHandle("baz", SolidHandle("bar", None))
    assert handle.pop(SolidHandle("bar", SolidHandle("foo", None))) == SolidHandle("baz", None)

    with pytest.raises(CheckError, match="does not descend from"):
        handle = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", None)))
        handle.pop(SolidHandle("quux", None))


def test_with_ancestor():
    handle = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", None)))
    assert handle.with_ancestor(None) == handle
    assert handle.with_ancestor(SolidHandle("quux", None)) == SolidHandle(
        "baz", SolidHandle("bar", SolidHandle("foo", SolidHandle("quux", None)))
    )


def test_dict_roundtrip():
    handle = SolidHandle("baz", SolidHandle("bar", SolidHandle("foo", None)))
    assert SolidHandle.from_dict(json.loads(json.dumps(handle._asdict()))) == handle

    handle = SolidHandle("foo", None)
    assert SolidHandle.from_dict(json.loads(json.dumps(handle._asdict()))) == handle
