"""Tests for serdes deduplication functionality."""

import json
from typing import NamedTuple

import pytest
from dagster_shared.record import record
from dagster_shared.serdes import (
    deserialize_value,
    serialize_value,
    serialize_value_with_dedup,
    whitelist_for_serdes,
)
from dagster_shared.serdes.errors import DeserializationError


@whitelist_for_serdes
@record
class Foo:
    name: str
    value: int


@whitelist_for_serdes
@record
class Bar:
    name: str
    other: Foo
    something: list[Foo]


@whitelist_for_serdes
class SimpleNT(NamedTuple):
    """Simple namedtuple for testing."""

    x: int
    y: str


@whitelist_for_serdes
@record
class NestedObject:
    item: SimpleNT
    items: list[SimpleNT]


def test_basic_deduplication():
    """Test that duplicate objects are deduplicated."""
    the_foo = Foo(name="foo", value=1)

    my_object = Bar(
        name="hello",
        other=the_foo,
        something=[the_foo, the_foo, the_foo],
    )

    # Serialize with dedup
    serialized = serialize_value_with_dedup(my_object)
    parsed = json.loads(serialized)

    # Should have deduplication marker
    assert parsed["__deduplication__"] is True
    assert "__dedup_table__" in parsed

    # The dedup table should have one entry (for the_foo)
    dedup_table = parsed["__dedup_table__"]
    assert len(dedup_table) == 1

    # The first occurrence (in 'other') should be serialized in-place
    assert parsed["value"]["other"]["__class__"] == "Foo"
    assert parsed["value"]["other"]["name"] == "foo"

    # The subsequent occurrences should be references
    something_list = parsed["value"]["something"]
    assert len(something_list) == 3
    for item in something_list:
        assert "__dedup_ref__" in item
        # All should reference the same hash
        assert item["__dedup_ref__"] == something_list[0]["__dedup_ref__"]

    # Deserialize and verify
    deserialized = deserialize_value(serialized, Bar)
    assert deserialized.name == "hello"
    assert deserialized.other.name == "foo"
    assert deserialized.other.value == 1
    assert len(deserialized.something) == 3
    for item in deserialized.something:
        assert item.name == "foo"
        assert item.value == 1


def test_no_duplicates_no_dedup_table():
    """Test that when there are no duplicates, no dedup table is created."""
    foo1 = Foo(name="foo1", value=1)
    foo2 = Foo(name="foo2", value=2)
    foo3 = Foo(name="foo3", value=3)

    my_object = Bar(
        name="unique",
        other=foo1,
        something=[foo2, foo3],
    )

    serialized = serialize_value_with_dedup(my_object)
    parsed = json.loads(serialized)

    # Should not have deduplication marker or table since no duplicates
    assert "__deduplication__" not in parsed or parsed.get("__deduplication__") is False
    assert "__dedup_table__" not in parsed


def test_content_hash_deduplication():
    """Test that objects with same content are deduplicated even if different instances."""
    foo1 = Foo(name="foo", value=1)
    foo2 = Foo(name="foo", value=1)  # Same content, different instance

    my_object = Bar(
        name="content_hash",
        other=foo1,
        something=[foo2, foo1],
    )

    serialized = serialize_value_with_dedup(my_object)
    parsed = json.loads(serialized)

    # Should deduplicate based on content
    assert parsed["__deduplication__"] is True
    assert len(parsed["__dedup_table__"]) == 1

    # Verify round-trip
    deserialized = deserialize_value(serialized, Bar)
    assert deserialized.other.name == "foo"
    assert deserialized.something[0].name == "foo"
    assert deserialized.something[1].name == "foo"


def test_nested_deduplication():
    """Test deduplication works with nested structures."""
    simple = SimpleNT(x=42, y="test")

    nested = NestedObject(
        item=simple,
        items=[simple, simple, simple],
    )

    serialized = serialize_value_with_dedup(nested)
    parsed = json.loads(serialized)

    assert parsed["__deduplication__"] is True
    assert len(parsed["__dedup_table__"]) == 1

    deserialized = deserialize_value(serialized, NestedObject)
    assert deserialized.item.x == 42
    assert len(deserialized.items) == 3
    for item in deserialized.items:
        assert item.x == 42
        assert item.y == "test"


def test_list_with_many_duplicates():
    """Test deduplication with many repeated objects."""
    foo = Foo(name="repeated", value=99)

    # Create a list with the same object repeated many times
    my_list = [foo] * 100

    serialized = serialize_value_with_dedup(my_list)
    parsed = json.loads(serialized)

    assert parsed["__deduplication__"] is True
    # First occurrence is in-place, rest are references
    assert parsed["value"][0]["__class__"] == "Foo"

    # Check that subsequent items are references
    for i in range(1, 100):
        assert "__dedup_ref__" in parsed["value"][i]

    # Verify deserialization
    deserialized = deserialize_value(serialized, list)
    assert len(deserialized) == 100
    for item in deserialized:
        assert item.name == "repeated"
        assert item.value == 99


def test_dict_with_duplicate_values():
    """Test deduplication in dictionary values."""
    foo = Foo(name="shared", value=123)

    my_dict = {
        "a": foo,
        "b": foo,
        "c": foo,
        "d": Foo(name="unique", value=456),
    }

    serialized = serialize_value_with_dedup(my_dict)
    parsed = json.loads(serialized)

    assert parsed["__deduplication__"] is True

    # Verify deserialization
    deserialized = deserialize_value(serialized, dict)
    assert deserialized["a"].name == "shared"
    assert deserialized["b"].name == "shared"
    assert deserialized["c"].name == "shared"
    assert deserialized["d"].name == "unique"


def test_regular_deserialize_handles_dedup_format():
    """Test that regular deserialize_value automatically handles dedup format."""
    foo = Foo(name="test", value=1)
    bar = Bar(name="bar", other=foo, something=[foo, foo])

    # Serialize with dedup
    serialized_with_dedup = serialize_value_with_dedup(bar)

    # Regular deserialize_value should handle it
    deserialized = deserialize_value(serialized_with_dedup, Bar)

    assert deserialized.name == "bar"
    assert deserialized.other.name == "test"
    assert len(deserialized.something) == 2


def test_regular_serialize_still_works():
    """Test that regular serialize_value still works (no dedup)."""
    foo = Foo(name="test", value=1)
    bar = Bar(name="bar", other=foo, something=[foo, foo])

    # Regular serialize (no dedup)
    serialized = serialize_value(bar)
    parsed = json.loads(serialized)

    # Should not have dedup markers
    assert "__deduplication__" not in parsed
    assert "__dedup_table__" not in parsed

    # Each foo should be fully serialized
    assert parsed["other"]["__class__"] == "Foo"
    for item in parsed["something"]:
        assert item["__class__"] == "Foo"
        assert "__dedup_ref__" not in item


def test_different_objects_not_deduplicated():
    """Test that objects with different content are not deduplicated."""
    foo1 = Foo(name="foo1", value=1)
    foo2 = Foo(name="foo2", value=2)

    my_object = Bar(
        name="different",
        other=foo1,
        something=[foo1, foo2, foo1],  # foo1 appears twice
    )

    serialized = serialize_value_with_dedup(my_object)
    parsed = json.loads(serialized)

    assert parsed["__deduplication__"] is True
    # Should have 2 entries in dedup table (foo1 and foo2)
    # Actually, first occurrence of foo1 is in-place, second is in table
    # foo2 appears once, so it's in-place
    # So the table should have 1 entry for foo1's second occurrence
    dedup_table = parsed["__dedup_table__"]
    assert len(dedup_table) == 1  # Only foo1's duplicate

    deserialized = deserialize_value(serialized, Bar)
    assert deserialized.other.name == "foo1"
    assert deserialized.something[0].name == "foo1"
    assert deserialized.something[1].name == "foo2"
    assert deserialized.something[2].name == "foo1"


def test_empty_collections():
    """Test deduplication with empty collections."""
    bar = Bar(name="empty", other=Foo(name="foo", value=1), something=[])

    serialized = serialize_value_with_dedup(bar)
    deserialized = deserialize_value(serialized, Bar)

    assert deserialized.name == "empty"
    assert deserialized.something == []


def test_none_values():
    """Test that None values work correctly."""

    @whitelist_for_serdes
    @record
    class OptionalBar:
        name: str
        optional_foo: Foo | None

    obj = OptionalBar(name="test", optional_foo=None)

    serialized = serialize_value_with_dedup(obj)
    deserialized = deserialize_value(serialized, OptionalBar)

    assert deserialized.name == "test"
    assert deserialized.optional_foo is None


def test_invalid_dedup_reference():
    """Test that invalid dedup references raise errors."""
    # Manually construct invalid dedup data
    invalid_json = json.dumps(
        {
            "__deduplication__": True,
            "value": {"__dedup_ref__": "nonexistent_hash"},
            "__dedup_table__": {},
        }
    )

    with pytest.raises(DeserializationError, match="not found in dedup table"):
        deserialize_value(invalid_json)


def test_deeply_nested_structures():
    """Test deduplication with deeply nested structures."""
    foo = Foo(name="deep", value=1)

    deep_structure = {
        "level1": {
            "level2": {
                "level3": [
                    {"foo": foo},
                    {"foo": foo},
                    {"list": [foo, foo, foo]},
                ]
            }
        }
    }

    serialized = serialize_value_with_dedup(deep_structure)
    parsed = json.loads(serialized)

    assert parsed["__deduplication__"] is True

    deserialized = deserialize_value(serialized, dict)
    assert deserialized["level1"]["level2"]["level3"][0]["foo"].name == "deep"
    assert deserialized["level1"]["level2"]["level3"][1]["foo"].name == "deep"
