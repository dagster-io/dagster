import dagster as dg
from dagster import AutomationCondition, DagsterInstance
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.automation_tick_evaluation_context import (
    _chunked_entity_keys_for_runs,
    build_run_requests,
)


def _asset_key(i: int) -> AssetKey:
    return AssetKey(f"asset_{i:03}")


def test_chunked_entity_keys_for_runs() -> None:
    keys = [_asset_key(i) for i in range(10)]
    # intentionally unsorted input, so the sort-ordering assertions below are not vacuous
    shuffled = list(reversed(keys))

    # no limit -> single chunk containing everything, in the original (unsorted) order
    assert _chunked_entity_keys_for_runs(shuffled, None) == [shuffled]

    # at or under the limit -> single chunk, in deterministic (sorted) order
    assert _chunked_entity_keys_for_runs(shuffled, 10) == [keys]

    chunks = _chunked_entity_keys_for_runs(shuffled, 4)
    assert [len(chunk) for chunk in chunks] == [4, 4, 2]
    # deterministic ordering (unsorted input -> sorted output), disjoint, complete
    assert [key for chunk in chunks for key in chunk] == keys

    # check keys ride with their asset, even if the unit exceeds the limit
    check_keys = [AssetCheckKey(_asset_key(0), f"check_{i}") for i in range(4)]
    chunks = _chunked_entity_keys_for_runs([*keys[:3], *check_keys], 3)
    assert [len(chunk) for chunk in chunks] == [5, 2]
    assert chunks[0][0] == _asset_key(0)
    assert set(chunks[0][1:]) == set(check_keys)

    # a check key whose asset is not requested becomes its own unit
    orphan_check_key = AssetCheckKey(AssetKey("not_requested"), "check")
    chunks = _chunked_entity_keys_for_runs([*keys[:2], orphan_check_key], 2)
    assert [len(chunk) for chunk in chunks] == [2, 1]
    assert chunks[-1] == [orphan_check_key]


def _build_defs(num_assets: int) -> dg.Definitions:
    assets = []
    for i in range(num_assets):

        @dg.asset(name=f"asset_{i:03}", automation_condition=AutomationCondition.missing())
        def _the_asset() -> None: ...

        assets.append(_the_asset)
    return dg.Definitions(assets=assets)


def test_build_run_requests_max_entities_per_run() -> None:
    defs = _build_defs(12)
    result = dg.evaluate_automation_conditions(defs=defs, instance=DagsterInstance.ephemeral())
    entity_subsets = [r.true_subset for r in result.results if not r.true_subset.is_empty]
    assert len(entity_subsets) == 12

    # without a limit: a single run targeting everything
    run_requests = build_run_requests(
        entity_subsets=entity_subsets,
        asset_graph=defs.resolve_asset_graph(),
        run_tags={},
        emit_backfills=False,
    )
    assert len(run_requests) == 1

    # with a limit: deterministic chunks of at most 5
    run_requests = build_run_requests(
        entity_subsets=entity_subsets,
        asset_graph=defs.resolve_asset_graph(),
        run_tags={"foo": "bar"},
        emit_backfills=False,
        max_entities_per_run=5,
    )
    assert [len(run_request.asset_selection or []) for run_request in run_requests] == [5, 5, 2]
    all_keys = [key for run_request in run_requests for key in (run_request.asset_selection or [])]
    assert len(set(all_keys)) == 12
    assert all(run_request.tags.get("foo") == "bar" for run_request in run_requests)


def test_max_entities_per_run_metadata_round_trip() -> None:
    # The asset daemon reads max_entities_per_run back from the sensor's stored metadata when the
    # sensor is not evaluated in the user code server. Guard that round-trip so a regression in the
    # metadata key or value type does not silently disable chunking.
    sensor = dg.AutomationConditionSensorDefinition(
        "s", target=dg.AssetSelection.all(), max_entities_per_run=5
    )
    assert sensor.max_entities_per_run == 5

    unset = dg.AutomationConditionSensorDefinition("s2", target=dg.AssetSelection.all())
    assert unset.max_entities_per_run is None
