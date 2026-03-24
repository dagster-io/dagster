"""Tests for compressed columnar packing (dagster_shared.serdes.pack)."""

import json
import os
import unittest.mock

import dagster as dg
from dagster import DagsterInstance
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes
from dagster_shared.serdes.pack import _TABLE_ROWS_KEY, deserialize_deduped, serialize_deduped
from dagster_shared.serdes.serdes import WhitelistMap, _whitelist_for_serdes


def test_round_trip_simple():
    """Round-trips a simple object through columnar packing."""

    @whitelist_for_serdes
    @record
    class Simple:
        x: int
        y: str

    obj = Simple(x=1, y="hello")
    packed_json = serialize_deduped(obj)
    result = deserialize_deduped(packed_json, as_type=Simple)
    assert result == obj


def test_always_columnar_envelope():
    """serialize_deduped always writes the columnar envelope format."""

    @whitelist_for_serdes
    @record
    class Leaf:
        x: int

    obj = Leaf(x=1)
    packed_json = serialize_deduped(obj)
    parsed = json.loads(packed_json)
    assert parsed["__columnar__"] is True
    assert "tables" in parsed
    assert "value" in parsed


def test_deduplication():
    """Identical objects share a single row in the columnar table."""
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Inner:
        number: float

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Foo:
        name: str
        value: int
        inner: Inner

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Bar:
        name: str
        single: Foo
        multiple: list[Foo]

    f1 = Foo(name="f1", value=1, inner=Inner(number=1.0))
    f1_dup = Foo(name="f1", value=1, inner=Inner(number=1.0))  # same content, different instance
    f2 = Foo(name="f2", value=2, inner=Inner(number=2.0))

    bar = Bar(name="bar", single=f1, multiple=[f1, f1_dup, f1_dup, f2])

    packed_json = serialize_deduped(bar, whitelist_map=test_map)

    # Tables are a list; find the Foo and Inner tables by class name
    parsed = json.loads(packed_json)
    tables = parsed["tables"]
    assert isinstance(tables, list)
    foo_table = next(t for t in tables if t["c"] == "Foo")
    inner_table = next(t for t in tables if t["c"] == "Inner")

    foo_rows = foo_table[_TABLE_ROWS_KEY]
    inner_rows = inner_table[_TABLE_ROWS_KEY]
    assert len(foo_rows) == 2, f"Expected 2 unique Foo rows, got {len(foo_rows)}"
    assert len(inner_rows) == 2, f"Expected 2 unique Inner rows, got {len(inner_rows)}"

    # Verify round-trip correctness.
    result = deserialize_deduped(packed_json, whitelist_map=test_map)
    assert result == bar


def test_numeric_table_ids_in_oid():
    """__oid__ refs use numeric table IDs instead of class names."""
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Leaf:
        x: int

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Container:
        leaf: Leaf

    obj = Container(leaf=Leaf(x=1))
    packed_json = serialize_deduped(obj, whitelist_map=test_map)
    parsed = json.loads(packed_json)

    # All __oid__ refs should use numeric table IDs (e.g. "0:0", "1:0")
    def find_oids(v):
        if isinstance(v, dict):
            if "__oid__" in v:
                yield v["__oid__"]
            for child in v.values():
                yield from find_oids(child)
        elif isinstance(v, list):
            for item in v:
                yield from find_oids(item)

    oids = list(find_oids(parsed))
    for oid in oids:
        table_id, _row_idx = oid.split(":")
        assert table_id.isdigit(), f"Expected numeric table_id, got {table_id!r} in oid {oid!r}"


def test_schema_evolution_new_field_with_default():
    """Deserializing data from an older schema fills new fields with defaults.

    Scenario:
    1. Serialize an object with fields a: int, b: int
    2. Add a new field c: str = "hi" to the class
    3. Deserialize the old data — c should appear with value "hi"
    """
    test_map = WhitelistMap.create()

    # V1: original schema
    @_whitelist_for_serdes(whitelist_map=test_map, storage_name="Evolving")
    @record
    class EvolvingV1:
        a: int
        b: int

    obj = EvolvingV1(a=1, b=2)
    packed_json = serialize_deduped(obj, whitelist_map=test_map)

    # V2: new schema with an added field
    test_map_v2 = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map_v2, storage_name="Evolving")
    @record
    class EvolvingV2:
        a: int
        b: int
        c: str = "hi"

    result = deserialize_deduped(packed_json, whitelist_map=test_map_v2, as_type=EvolvingV2)
    assert result.a == 1
    assert result.b == 2
    assert result.c == "hi"


def test_schema_evolution_new_field_nested():
    """Schema evolution works for nested objects too."""
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map, storage_name="Child")
    @record
    class ChildV1:
        x: int

    @_whitelist_for_serdes(whitelist_map=test_map, storage_name="Parent")
    @record
    class ParentV1:
        child: ChildV1

    obj = ParentV1(child=ChildV1(x=10))
    packed_json = serialize_deduped(obj, whitelist_map=test_map)

    # V2: Child gains a new field
    test_map_v2 = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map_v2, storage_name="Child")
    @record
    class ChildV2:
        x: int
        label: str = "default"

    @_whitelist_for_serdes(whitelist_map=test_map_v2, storage_name="Parent")
    @record
    class ParentV2:
        child: ChildV2

    result = deserialize_deduped(packed_json, whitelist_map=test_map_v2, as_type=ParentV2)
    assert result.child.x == 10
    assert result.child.label == "default"


def test_schema_evolution_removed_field():
    """Deserializing data that has extra fields from an older schema drops them."""
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map, storage_name="Shrinking")
    @record
    class ShrinkingV1:
        a: int
        b: int
        c: str

    obj = ShrinkingV1(a=1, b=2, c="gone")
    packed_json = serialize_deduped(obj, whitelist_map=test_map)

    # V2: field c removed
    test_map_v2 = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map_v2, storage_name="Shrinking")
    @record
    class ShrinkingV2:
        a: int
        b: int

    result = deserialize_deduped(packed_json, whitelist_map=test_map_v2, as_type=ShrinkingV2)
    assert result.a == 1
    assert result.b == 2


def test_columnar_classes_limits_which_classes_are_packed():
    """Only classes in columnar_classes get packed into tables; others are inline."""
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Leaf:
        x: int

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Middle:
        leaf: Leaf
        y: str

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Root:
        middle: Middle

    obj = Root(middle=Middle(leaf=Leaf(x=42), y="hello"))

    # Only pack Leaf into columnar tables
    packed_json = serialize_deduped(
        obj, whitelist_map=test_map, columnar_classes=frozenset({"Leaf"})
    )
    parsed = json.loads(packed_json)

    # Only Leaf should appear in tables
    table_classes = {t["c"] for t in parsed["tables"]}
    assert table_classes == {"Leaf"}

    # Root and Middle should be inline dicts with __class__ keys
    value = parsed["value"]
    assert value["__class__"] == "Root"
    assert value["middle"]["__class__"] == "Middle"
    # But Leaf should be an __oid__ ref
    assert "__oid__" in value["middle"]["leaf"]

    # Round-trip still works
    result = deserialize_deduped(packed_json, whitelist_map=test_map, as_type=Root)
    assert result == obj


def test_columnar_classes_empty_frozenset_packs_nothing():
    """An empty frozenset means no classes are columnar-packed — all inline."""
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Item:
        val: int

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Wrapper:
        items: list[Item]

    obj = Wrapper(items=[Item(val=1), Item(val=2)])
    packed_json = serialize_deduped(obj, whitelist_map=test_map, columnar_classes=frozenset())
    parsed = json.loads(packed_json)

    # No tables should be populated
    assert parsed["tables"] == []

    # Everything should be inline
    value = parsed["value"]
    assert value["__class__"] == "Wrapper"
    for item in value["items"]:
        assert item["__class__"] == "Item"
        assert "__oid__" not in item

    # Round-trip still works
    result = deserialize_deduped(packed_json, whitelist_map=test_map, as_type=Wrapper)
    assert result == obj


def test_columnar_classes_none_packs_everything():
    """columnar_classes=None (default) packs all classes into tables."""
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Alpha:
        a: int

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Beta:
        alpha: Alpha
        b: str

    obj = Beta(alpha=Alpha(a=1), b="hi")
    packed_json = serialize_deduped(obj, whitelist_map=test_map, columnar_classes=None)
    parsed = json.loads(packed_json)

    # Both classes should be in tables
    table_classes = {t["c"] for t in parsed["tables"]}
    assert table_classes == {"Alpha", "Beta"}

    # Top-level value should be an __oid__ ref, not inline
    assert "__oid__" in parsed["value"]

    result = deserialize_deduped(packed_json, whitelist_map=test_map, as_type=Beta)
    assert result == obj


def test_columnar_classes_dedup_still_works_for_packed_classes():
    """Deduplication works for classes in the columnar set; inline classes are not deduped."""
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Tag:
        name: str

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Entry:
        tag: Tag
        value: int

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Collection:
        entries: list[Entry]

    shared_tag = Tag(name="shared")
    obj = Collection(
        entries=[
            Entry(tag=shared_tag, value=1),
            Entry(tag=Tag(name="shared"), value=2),  # same content, different instance
            Entry(tag=Tag(name="unique"), value=3),
        ]
    )

    # Only pack Tag into tables; Entry and Collection stay inline
    packed_json = serialize_deduped(
        obj, whitelist_map=test_map, columnar_classes=frozenset({"Tag"})
    )
    parsed = json.loads(packed_json)

    # Tag table should have 2 unique rows ("shared" and "unique")
    tag_table = next(t for t in parsed["tables"] if t["c"] == "Tag")
    assert len(tag_table["r"]) == 2

    # Entry should NOT be in tables
    assert not any(t["c"] == "Entry" for t in parsed["tables"])

    # The two "shared" tags should reference the same oid
    entries = parsed["value"]["entries"]
    assert entries[0]["tag"] == entries[1]["tag"]  # same __oid__ ref
    assert entries[0]["tag"] != entries[2]["tag"]  # different tag

    result = deserialize_deduped(packed_json, whitelist_map=test_map, as_type=Collection)
    assert result == obj


def test_columnar_classes_with_nested_packed_inside_inline():
    """A packed class nested inside an inline class is still packed correctly."""
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Deep:
        z: int

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Shallow:
        deep: Deep
        label: str

    obj = Shallow(deep=Deep(z=99), label="test")

    # Only Deep is columnar-packed; Shallow is inline
    packed_json = serialize_deduped(
        obj, whitelist_map=test_map, columnar_classes=frozenset({"Deep"})
    )
    parsed = json.loads(packed_json)

    # Shallow is inline
    assert parsed["value"]["__class__"] == "Shallow"
    assert parsed["value"]["label"] == "test"
    # Deep is an oid ref inside the inline Shallow
    assert "__oid__" in parsed["value"]["deep"]

    result = deserialize_deduped(packed_json, whitelist_map=test_map, as_type=Shallow)
    assert result == obj


def _make_cursor(num_upstream: int = 20) -> AssetDaemonCursor:
    """Create a realistic cursor with many assets sharing the same partition def."""
    daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")

    upstream_assets = []
    for i in range(num_upstream):

        @dg.asset(partitions_def=daily_partitions, name=f"upstream_{i}")
        def _upstream() -> None: ...

        upstream_assets.append(_upstream)

    @dg.asset(
        deps=upstream_assets,
        automation_condition=dg.AutomationCondition.on_cron(cron_schedule="0 * * * *"),
    )
    def downstream() -> None: ...

    defs = dg.Definitions(assets=[*upstream_assets, downstream])
    instance = DagsterInstance.ephemeral()

    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    cursor = result.cursor
    assert isinstance(cursor, AssetDaemonCursor)
    return cursor


def test_cursor_round_trip():
    """Round-trips a real AssetDaemonCursor through columnar packing."""
    cursor = _make_cursor(num_upstream=10)

    packed_json = serialize_deduped(cursor)
    result = deserialize_deduped(packed_json, as_type=AssetDaemonCursor)
    assert result == cursor


def test_instigator_cursor_reads_both_versions():
    """The reader handles both v0 (plain serdes) and v1 (columnar-packed) cursors."""
    from dagster._daemon.asset_daemon import (
        asset_daemon_cursor_from_instigator_serialized_cursor,
        asset_daemon_cursor_to_instigator_serialized_cursor,
    )

    cursor = _make_cursor(num_upstream=10)

    # Default writer produces version "0"
    v0_stored = asset_daemon_cursor_to_instigator_serialized_cursor(cursor)
    assert v0_stored.startswith("0")

    # With env var set, writer produces version "1"
    with unittest.mock.patch.dict(
        os.environ, {"DAGSTER_WRITE_COMPRESSED_ASSET_DAEMON_CURSOR": "1"}
    ):
        v1_stored = asset_daemon_cursor_to_instigator_serialized_cursor(cursor)
    assert v1_stored.startswith("1")

    # Both should deserialize to the same cursor
    from_v0 = asset_daemon_cursor_from_instigator_serialized_cursor(v0_stored, None)
    from_v1 = asset_daemon_cursor_from_instigator_serialized_cursor(v1_stored, None)

    assert from_v0 == cursor
    assert from_v1 == cursor
