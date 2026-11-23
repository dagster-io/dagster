import dataclasses
import json
import re
from enum import Enum
from typing import Any, NamedTuple

import dagster as dg
import pydantic
import pytest
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._serdes import deserialize_value, serialize_value
from dagster_shared.serdes.compact import dumps_compact, is_compact_serialized, loads_compact
from dagster_shared.serdes.errors import DeserializationError, SerializationError
from dagster_shared.serdes.serdes import (
    FieldSerializer,
    PackedObjects,
    WhitelistMap,
    _whitelist_for_serdes,
    pack_value,
)

VALUES = [
    None,
    True,
    False,
    0,
    -3,
    1.5,
    1.0,
    10**30,
    "",
    "plain string",
    [],
    {},
    [1, 1.0, True, "1", None],
    {"a": 1, "__class__x": "not a class"},
    {"nested": [{"x": [1, 2, {"y": "long repeated string value"}]}] * 3},
    {"__set__": ["a", "b"]},
    [[0, 1], [1, 2], [2], [3, "x"]],
]


@pytest.mark.parametrize("value", VALUES)
def test_packed_roundtrip(value) -> None:
    serialized = dumps_compact(value)
    assert is_compact_serialized(serialized)
    assert loads_compact(serialized, lambda d: d) == value
    assert loads_compact(serialized, lambda d: d, expand=True) == value
    # numbers keep their type
    assert json.dumps(loads_compact(serialized, lambda d: d)) == json.dumps(value)


def test_object_roundtrip_and_sharing() -> None:
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Color(Enum):
        RED = "RED"

    @_whitelist_for_serdes(whitelist_map=test_map, storage_field_names={"inner": "old_inner"})
    class Leaf(NamedTuple):
        keys: list[str]
        color: Color
        tags: frozenset[str]

    @_whitelist_for_serdes(whitelist_map=test_map, old_fields={"removed": None})
    class Node(NamedTuple):
        name: str
        inner: Leaf
        other: Leaf

    leaf = Leaf([f"partition-{i}" for i in range(100)], Color.RED, frozenset({"a"}))
    value = [Node(f"node-{i}", leaf, Leaf([], Color.RED, frozenset())) for i in range(50)]

    legacy = dg.serialize_value(value, whitelist_map=test_map)
    compact = dg.serialize_value(value, whitelist_map=test_map, compact=True)
    assert len(compact) * 10 < len(legacy)

    deserialized = dg.deserialize_value(compact, whitelist_map=test_map)
    assert deserialized == value
    assert deserialized == dg.deserialize_value(legacy, whitelist_map=test_map)
    # equal subtrees decode to a single shared object
    assert deserialized[0].inner is deserialized[1].inner


@pytest.mark.parametrize("dropped_first", [False, True])
def test_unknown_values(dropped_first: bool) -> None:
    def serialize_with_new_classes(kept_shared: bool) -> str:
        new_map = WhitelistMap.create()

        @_whitelist_for_serdes(whitelist_map=new_map)
        class Removed(NamedTuple):
            value: str

        if dropped_first:

            @_whitelist_for_serdes(whitelist_map=new_map)
            class Holder(NamedTuple):  # pyright: ignore[reportRedeclaration]
                dropped: Removed
                kept: list[Removed]

        else:

            @_whitelist_for_serdes(whitelist_map=new_map)
            class Holder(NamedTuple):
                kept: list[Removed]
                dropped: Removed

        shared = Removed("shared value that is long enough")
        kept = [shared] if kept_shared else []
        return dg.serialize_value(
            Holder(kept=kept, dropped=shared), whitelist_map=new_map, compact=True
        )

    old_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=old_map)
    class Holder(NamedTuple):
        kept: list

    # the same unknown subtree is under both an ignored field and a kept field
    with pytest.raises(DeserializationError, match="not in the whitelist"):
        dg.deserialize_value(serialize_with_new_classes(kept_shared=True), whitelist_map=old_map)

    # unknown values under fields that the reader ignores are dropped
    assert dg.deserialize_value(
        serialize_with_new_classes(kept_shared=False), whitelist_map=old_map
    ) == Holder([])


def test_repository_snap_roundtrip() -> None:
    @dg.asset(
        partitions_def=dg.StaticPartitionsDefinition(["a", "b"]),
        check_specs=[
            dg.AssetCheckSpec(
                name=f"check_{i}",
                asset="partitioned",
                partitions_def=dg.StaticPartitionsDefinition(["a", "b"]),
            )
            for i in range(3)
        ],
        metadata={"owner_url": dg.MetadataValue.url("http://example.com")},
    )
    def partitioned(): ...

    @dg.asset(deps=[partitioned], automation_condition=dg.AutomationCondition.eager())
    def downstream(): ...

    repo = dg.Definitions(assets=[partitioned, downstream]).get_repository_def()
    snap = RepositorySnap.from_def(repo, defer_snapshots=True)
    compact = serialize_value(snap, compact=True)
    legacy = serialize_value(snap)
    assert deserialize_value(compact, RepositorySnap) == deserialize_value(legacy, RepositorySnap)
    assert json.loads(legacy) == loads_compact(compact, lambda d: d)
    assert pack_value(deserialize_value(compact, RepositorySnap)) == json.loads(legacy)


def _assert_compact_matches_legacy(value, whitelist_map) -> None:
    legacy = dg.serialize_value(value, whitelist_map=whitelist_map)
    compact = dg.serialize_value(value, whitelist_map=whitelist_map, compact=True)
    assert loads_compact(compact, lambda d: d) == json.loads(legacy)
    assert dg.deserialize_value(compact, whitelist_map=whitelist_map) == dg.deserialize_value(
        legacy, whitelist_map=whitelist_map
    )


def test_packer_matches_legacy_for_serializer_features() -> None:
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Color(Enum):
        RED = "RED"
        BLUE = "BLUE"

    class UpperFieldSerializer(FieldSerializer):
        def pack(self, value, whitelist_map, descent_path):
            return value.upper()

        def unpack(self, value, whitelist_map, context):
            return value.lower()

    class EntriesFieldSerializer(FieldSerializer):
        def pack(self, value, whitelist_map, descent_path):
            return [
                {"__class__": "Entry", "key": k, "value": pack_value(v, whitelist_map)}
                for k, v in value.items()
            ]

        def pack_shallow(self, value, whitelist_map):
            return PackedObjects("Entry", ("key", "value"), [(k, v) for k, v in value.items()])

        def unpack(self, value, whitelist_map, context):
            return {entry.key: entry.value for entry in value}

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Entry(NamedTuple):
        key: str
        value: Any

    @_whitelist_for_serdes(
        whitelist_map=test_map,
        storage_name="OldName",
        storage_field_names={"renamed": "old_renamed"},
        old_fields={"removed": None},
        skip_when_empty_fields={"maybe_empty"},
        skip_when_none_fields={"maybe_none"},
        field_serializers={"upper": UpperFieldSerializer, "entries": EntriesFieldSerializer},
    )
    class Obj(NamedTuple):
        renamed: str
        upper: str
        entries: dict
        color: Color
        tags: frozenset
        maybe_empty: list = []
        maybe_none: str | None = None

    @_whitelist_for_serdes(
        whitelist_map=test_map,
        skip_when_empty_fields={"entries"},
        field_serializers={"entries": EntriesFieldSerializer},
    )
    class SkippedEntries(NamedTuple):
        name: str
        entries: dict = {}

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Plain(NamedTuple):
        first: str
        second: int | None
        third: bool

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Model(pydantic.BaseModel):
        name: str
        items: list[str]

    @_whitelist_for_serdes(whitelist_map=test_map)
    @dataclasses.dataclass
    class Data:
        values: list[int]
        model: Model

    objects = [
        Obj(
            renamed=f"r{i}",
            upper="abc",
            entries={"a": Color.RED, "b": i, "c": None} if i % 2 else {},
            maybe_empty=[] if i % 3 else ["x"],
            maybe_none=None if i % 2 else "set",
            color=Color.BLUE if i % 2 else Color.RED,
            tags=frozenset({"t1", "t2"}),
        )
        for i in range(250)  # more objects than sampled before memoization is turned off
    ]
    shared_model = Model(name="shared", items=["a", "b", "c"])
    value = {
        "objects": objects,
        "repeated": [objects[0]] * 3,
        "models": [Model(name=f"m{i}", items=["x"] * (i % 4)) for i in range(250)],
        "shared_models": [shared_model] * 250,
        "data": [Data(values=[1, 2.5, 3], model=shared_model)] * 2,
        "skipped_entries": [SkippedEntries(name="a"), SkippedEntries(name="b", entries={"k": 1})],
        # distinct objects: memoization is turned off for the type, after sampling
        "plain": [
            Plain(first=f"p{i}", second=i if i % 2 else None, third=i % 3 == 0) for i in range(250)
        ],
        "nested": {"tuple": (1, "a", None), "set": {"b", "a"}},
        # json.dumps converts non-str scalar keys to str
        "int_keys": {3: True, 1: 1.0},
    }
    _assert_compact_matches_legacy(value, test_map)


def test_packer_serialization_errors_have_descent_paths() -> None:
    test_map = WhitelistMap.create()

    class NotWhitelisted(NamedTuple):
        x: int

    with pytest.raises(SerializationError, match=re.escape("Descent path: <root:dict>.a[1]")):
        dg.serialize_value({"a": [1, NotWhitelisted(1)]}, whitelist_map=test_map, compact=True)


def test_compact_snapshot_of_large_repository() -> None:
    assets = [
        dg.AssetSpec(
            key=["group", f"asset_{i}"],
            metadata={"url": dg.MetadataValue.url(f"http://x/{i}"), "count": i},
            partitions_def=dg.StaticPartitionsDefinition([f"p{j}" for j in range(i % 5 + 1)]),
        )
        for i in range(1200)  # more than streamed when writing
    ]
    repo = dg.Definitions(assets=assets).get_repository_def()
    snap = RepositorySnap.from_def(repo, defer_snapshots=True)
    compact = serialize_value(snap, compact=True)
    legacy = serialize_value(snap)
    assert loads_compact(compact, lambda d: d) == json.loads(legacy)
