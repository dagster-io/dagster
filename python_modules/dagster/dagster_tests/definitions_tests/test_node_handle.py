import pytest
from dagster._check import CheckError
from dagster._core.definitions.dependency import NodeHandle
from dagster._seven import json


def test_handle_path():
    handle = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", None)))
    assert handle.path == ["foo", "bar", "baz"]
    assert NodeHandle.from_path(handle.path) == handle

    handle = NodeHandle("foo", None)
    assert handle.path == ["foo"]
    assert NodeHandle.from_path(handle.path) == handle


def test_handle_to_from_string():
    handle = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", None)))
    assert str(handle) == "foo.bar.baz"
    assert NodeHandle.from_string(str(handle)) == handle

    handle = NodeHandle("foo", None)
    assert str(handle) == "foo"
    assert NodeHandle.from_string(str(handle)) == handle


def test_is_or_descends_from():
    ancestor = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", NodeHandle("quux", None))))
    descendant = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", None)))
    assert not descendant.is_or_descends_from(ancestor)

    ancestor = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", None)))
    descendant = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", None)))
    assert descendant.is_or_descends_from(ancestor)

    ancestor = NodeHandle("bar", NodeHandle("foo", None))
    descendant = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", None)))
    assert descendant.is_or_descends_from(ancestor)

    ancestor = NodeHandle("foo", None)
    descendant = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", None)))
    assert descendant.is_or_descends_from(ancestor)

    ancestor = NodeHandle("foo", None)
    descendant = NodeHandle("foo", None)
    assert descendant.is_or_descends_from(ancestor)

    ancestor = NodeHandle("foo", None)
    descendant = NodeHandle("bar", None)
    assert not descendant.is_or_descends_from(ancestor)

    ancestor = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", None)))
    descendant = NodeHandle("baz", None)
    assert not descendant.is_or_descends_from(ancestor)

    ancestor = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", None)))
    descendant = NodeHandle("baz", NodeHandle("bar", None))
    assert not descendant.is_or_descends_from(ancestor)


def test_pop():
    handle = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", None)))
    assert handle.pop_ancestor(NodeHandle("foo", None)) == NodeHandle(
        "baz", NodeHandle("bar", None)
    )
    assert handle.pop_ancestor(NodeHandle("bar", NodeHandle("foo", None))) == NodeHandle(
        "baz", None
    )

    with pytest.raises(CheckError, match="does not descend from"):
        handle = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", None)))
        handle.pop_ancestor(NodeHandle("quux", None))


def test_with_child():
    handle = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", None)))
    assert handle.with_child(None) == handle
    assert NodeHandle("quux", None).with_child(handle) == NodeHandle(
        "baz", NodeHandle("bar", NodeHandle("foo", NodeHandle("quux", None)))
    )


def test_dict_roundtrip():
    handle = NodeHandle("baz", NodeHandle("bar", NodeHandle("foo", None)))
    assert NodeHandle.from_dict(json.loads(json.dumps(handle._asdict()))) == handle

    handle = NodeHandle("foo", None)
    assert NodeHandle.from_dict(json.loads(json.dumps(handle._asdict()))) == handle
