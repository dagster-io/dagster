"""Unit tests for the materialization health state objects, focused on the WARNING
(up-for-retry) status derivation added alongside up_for_retry_subsets_by_run_id /
num_up_for_retry_partitions.
"""

import dagster as dg
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_health.asset_health import AssetHealthStatus
from dagster._core.definitions.asset_health.asset_materialization_health import (
    AssetMaterializationHealthState,
    MinimalAssetMaterializationHealthState,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.partitions.snap import PartitionsSnap
from dagster._serdes import deserialize_value, serialize_value

AK = AssetKey("a")
PARTITIONS_DEF = dg.StaticPartitionsDefinition(["1", "2", "3"])

# ########################
# ##### TESTS
# ########################


def test_non_partitioned_health_status():
    # no materializations or failures -> UNKNOWN
    assert (
        _np_state(materialized=False, failed=False, up_for_retry=None).health_status
        == AssetHealthStatus.UNKNOWN
    )
    # materialized and not failed -> HEALTHY
    assert (
        _np_state(materialized=True, failed=False, up_for_retry=None).health_status
        == AssetHealthStatus.HEALTHY
    )
    # failed with up-for-retry state untracked (None) or empty -> DEGRADED
    assert (
        _np_state(materialized=True, failed=True, up_for_retry=None).health_status
        == AssetHealthStatus.DEGRADED
    )
    assert (
        _np_state(materialized=True, failed=True, up_for_retry=False).health_status
        == AssetHealthStatus.DEGRADED
    )
    # failed but the failing run is up for retry -> WARNING
    assert (
        _np_state(materialized=True, failed=True, up_for_retry=True).health_status
        == AssetHealthStatus.WARNING
    )
    # never materialized but failed and up for retry -> still WARNING
    assert (
        _np_state(materialized=False, failed=True, up_for_retry=True).health_status
        == AssetHealthStatus.WARNING
    )


def test_num_up_for_retry_partitions_clamped_to_failed():
    # untracked -> 0
    assert (
        _np_state(materialized=True, failed=True, up_for_retry=None).num_up_for_retry_partitions
        == 0
    )
    # up_for_retry set but nothing is actually failed -> intersection is empty -> 0
    assert (
        _np_state(materialized=True, failed=False, up_for_retry=True).num_up_for_retry_partitions
        == 0
    )
    # up_for_retry includes a partition (3) that is not currently failed -> clamped via
    # intersection; status is still WARNING because all failed partitions are covered
    state = _partitioned_state(
        materialized=("1", "2"), failed=("1", "2"), up_for_retry={"r1": ("1", "2", "3")}
    )
    assert state.health_status == AssetHealthStatus.WARNING
    assert state.num_up_for_retry_partitions == 2
    # the subset itself is clamped, so it is consistent with the count: partition 3 is excluded
    up_for_retry_subset = state.up_for_retry_subset
    assert up_for_retry_subset is not None
    assert up_for_retry_subset.compute_difference(state.failed_subset).is_empty
    assert state.failed_subset.compute_difference(up_for_retry_subset).is_empty


def test_partitioned_health_status():
    # all failed partitions up for retry -> WARNING
    state = _partitioned_state(
        materialized=("1", "2"), failed=("1", "2"), up_for_retry={"r1": ("1", "2")}
    )
    assert state.health_status == AssetHealthStatus.WARNING
    assert state.num_up_for_retry_partitions == 2

    # a failed partition not up for retry -> DEGRADED dominates
    state = _partitioned_state(
        materialized=("1", "2"), failed=("1", "2"), up_for_retry={"r1": ("1",)}
    )
    assert state.health_status == AssetHealthStatus.DEGRADED
    assert state.num_up_for_retry_partitions == 1

    # empty tracked mapping (no pending retries) -> DEGRADED
    state = _partitioned_state(materialized=("1", "2"), failed=("1", "2"), up_for_retry={})
    assert state.health_status == AssetHealthStatus.DEGRADED
    assert state.num_up_for_retry_partitions == 0


def test_up_for_retry_union_across_runs():
    # two runs each cover part of the failed subset; the union covers all of it -> WARNING
    state = _partitioned_state(
        materialized=(),
        failed=("1", "2", "3"),
        up_for_retry={"r1": ("1",), "r2": ("2", "3")},
    )
    assert state.health_status == AssetHealthStatus.WARNING
    assert state.num_up_for_retry_partitions == 3
    # overlapping subsets are not double counted
    state = _partitioned_state(
        materialized=(),
        failed=("1", "2"),
        up_for_retry={"r1": ("1", "2"), "r2": ("2",)},
    )
    assert state.num_up_for_retry_partitions == 2
    # union covering only part of the failed subset -> DEGRADED
    state = _partitioned_state(
        materialized=(),
        failed=("1", "2", "3"),
        up_for_retry={"r1": ("1",), "r2": ("2",)},
    )
    assert state.health_status == AssetHealthStatus.DEGRADED


def test_minimal_state_matches_full_state():
    for state in [
        _np_state(materialized=False, failed=False, up_for_retry=None),
        _np_state(materialized=True, failed=False, up_for_retry=None),
        _np_state(materialized=True, failed=True, up_for_retry=None),
        _np_state(materialized=True, failed=True, up_for_retry=True),
        _np_state(materialized=True, failed=True, up_for_retry=False),
        _partitioned_state(
            materialized=("1", "2"), failed=("1", "2"), up_for_retry={"r1": ("1", "2")}
        ),
        _partitioned_state(materialized=("1", "2"), failed=("1", "2"), up_for_retry={"r1": ("1",)}),
        _partitioned_state(materialized=("1", "2"), failed=("1", "2"), up_for_retry=None),
    ]:
        minimal = MinimalAssetMaterializationHealthState.from_asset_materialization_health_state(
            state
        )
        assert minimal.health_status == state.health_status
        assert minimal.num_up_for_retry_partitions == state.num_up_for_retry_partitions


def test_serdes_roundtrip_and_backcompat():
    # round-trip preserves up-for-retry state and WARNING derivation
    with_retry = _np_state(materialized=True, failed=True, up_for_retry=True)
    restored = deserialize_value(serialize_value(with_retry), AssetMaterializationHealthState)
    assert restored.up_for_retry_subsets_by_run_id is not None
    assert restored.health_status == AssetHealthStatus.WARNING

    # skip_when_none_fields: None is omitted from storage, matching pre-existing serialized
    # states. This is also the backcompat case: data lacking the key deserializes to None.
    without_retry = _np_state(materialized=True, failed=True, up_for_retry=None)
    serialized = serialize_value(without_retry)
    assert "up_for_retry_subsets_by_run_id" not in serialized
    assert (
        deserialize_value(
            serialized, AssetMaterializationHealthState
        ).up_for_retry_subsets_by_run_id
        is None
    )

    # minimal state: old payloads without the count default to 0 and stay DEGRADED
    minimal = MinimalAssetMaterializationHealthState(
        latest_materialization_timestamp=None,
        latest_terminal_run_id=None,
        num_failed_partitions=1,
        num_currently_materialized_partitions=0,
        partitions_snap=None,
    )
    assert minimal.num_up_for_retry_partitions == 0
    assert minimal.health_status == AssetHealthStatus.DEGRADED
    restored_minimal = deserialize_value(
        serialize_value(minimal), MinimalAssetMaterializationHealthState
    )
    assert restored_minimal.num_up_for_retry_partitions == 0


# ########################
# ##### HELPERS
# ########################


def _bool_subset(value: bool) -> SerializableEntitySubset[AssetKey]:
    return SerializableEntitySubset(key=AK, value=value)


def _partition_subset(*partition_keys: str) -> SerializableEntitySubset[AssetKey]:
    return SerializableEntitySubset(
        key=AK, value=PARTITIONS_DEF.subset_with_partition_keys(partition_keys)
    )


def _np_state(
    *, materialized: bool, failed: bool, up_for_retry: bool | None
) -> AssetMaterializationHealthState:
    """up_for_retry semantics: None => untracked; False => tracked with no pending retries;
    True => the failing run is pending a retry.
    """
    if up_for_retry is None:
        up_for_retry_subsets_by_run_id = None
    elif up_for_retry:
        up_for_retry_subsets_by_run_id = {"failed_run_id": _bool_subset(True)}
    else:
        up_for_retry_subsets_by_run_id = {}
    return AssetMaterializationHealthState(
        materialized_subset=_bool_subset(materialized),
        failed_subset=_bool_subset(failed),
        partitions_snap=None,
        latest_terminal_run_id=None,
        up_for_retry_subsets_by_run_id=up_for_retry_subsets_by_run_id,
    )


def _partitioned_state(
    *,
    materialized: tuple[str, ...],
    failed: tuple[str, ...],
    up_for_retry: dict[str, tuple[str, ...]] | None,
) -> AssetMaterializationHealthState:
    return AssetMaterializationHealthState(
        materialized_subset=_partition_subset(*materialized),
        failed_subset=_partition_subset(*failed),
        partitions_snap=PartitionsSnap.from_def(PARTITIONS_DEF),
        latest_terminal_run_id=None,
        up_for_retry_subsets_by_run_id={
            run_id: _partition_subset(*keys) for run_id, keys in up_for_retry.items()
        }
        if up_for_retry is not None
        else None,
    )
