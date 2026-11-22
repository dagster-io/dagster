import json
from enum import Enum
from typing import NamedTuple

import dagster as dg
import pytest
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._serdes import deserialize_value, serialize_value
from dagster_shared.serdes.compact import dumps_compact, is_compact_serialized, loads_compact
from dagster_shared.serdes.errors import DeserializationError
from dagster_shared.serdes.serdes import WhitelistMap, _whitelist_for_serdes, pack_value

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
