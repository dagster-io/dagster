import datetime

import dagster as dg
import pytest
from dagster import (
    AutomationCondition as AC,
    deserialize_value,
)
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_selection import AssetSelection

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.base_scenario import run_request
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import ScenarioSpec

one_parent = ScenarioSpec(asset_specs=[dg.AssetSpec("A"), dg.AssetSpec("downstream", deps=["A"])])
two_parents = ScenarioSpec(
    asset_specs=[dg.AssetSpec("A"), dg.AssetSpec("B"), dg.AssetSpec("downstream", deps=["A", "B"])]
)

daily_partitions = dg.DailyPartitionsDefinition(start_date="2020-01-01")
one_parent_daily = one_parent.with_asset_properties(partitions_def=daily_partitions)
two_parents_daily = two_parents.with_asset_properties(partitions_def=daily_partitions)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["expected_value_hash", "condition", "scenario_spec", "materialize_A"],
    [
        # cron condition returns a unique value hash if parents change, if schedule changes, if the
        # partitions def changes, or if an asset is materialized
        ("93a765c5052e9c0e26fbb97b11f31ea9", AC.on_cron("0 * * * *"), one_parent, False),
        ("c9fc208a4bd809418b372c28a7d33cba", AC.on_cron("0 * * * *"), one_parent, True),
        ("1e26dfd160b5d289156992e6e44e7959", AC.on_cron("0 0 * * *"), one_parent, False),
        ("aee5e2b0af668dfdde74f81d1b76773b", AC.on_cron("0 * * * *"), one_parent_daily, False),
        ("9d04ca345d1605f756f1f92f6a48a2a7", AC.on_cron("0 * * * *"), two_parents, False),
        ("98b9c46de1d70a4c3fd5f2a53b3207e6", AC.on_cron("0 * * * *"), two_parents_daily, False),
        # same as above
        ("c89e6e6cd095a5ed39bca4a566f3a988", AC.eager(), one_parent, False),
        ("3a3793b6b0267173caf31b043c836a1a", AC.eager(), one_parent, True),
        ("dd079a402386d1a5a750c6d12aa6af75", AC.eager(), one_parent_daily, False),
        (
            # note: identical hash to the above
            "dd079a402386d1a5a750c6d12aa6af75",
            AC.eager().allow(AssetSelection.all()),
            one_parent_daily,
            False,
        ),
        ("e83d9ec4cc577e786daa8acc1ee6bebb", AC.eager(), two_parents, False),
        ("aaf5f236045cb349300e500702e2676d", AC.eager(), two_parents_daily, False),
        # missing condition is invariant to changes other than partitions def changes
        ("6d7809c4949e3d812d7eddfb1b60d529", AC.missing(), one_parent, False),
        ("6d7809c4949e3d812d7eddfb1b60d529", AC.missing(), one_parent, True),
        ("6d7809c4949e3d812d7eddfb1b60d529", AC.missing(), two_parents, False),
        ("7f852ab7408c67e0830530d025505a37", AC.missing(), two_parents_daily, False),
        ("7f852ab7408c67e0830530d025505a37", AC.missing(), one_parent_daily, False),
    ],
)
async def test_value_hash(
    condition: AC, scenario_spec: ScenarioSpec, expected_value_hash: str, materialize_A: bool
) -> None:
    state = AutomationConditionScenarioState(
        scenario_spec, automation_condition=condition
    ).with_current_time("2024-01-01T00:00")

    state, _ = await state.evaluate("downstream")
    if materialize_A:
        state = state.with_runs(run_request("A"))

    state, result = await state.with_current_time("2024-01-01T01:00").evaluate("downstream")
    assert result.value_hash == expected_value_hash


@pytest.mark.parametrize(
    "sequence",
    [
        ["initial", "updated", "updated", "updated", "updated"],
        ["initial", "updated", "initial", "updated", "initial"],
        ["initial", "initial", "initial", "initial", "updated"],
    ],
)
def test_since_condition_memory(sequence: list[str]) -> None:
    downstream_key = dg.AssetKey("downstream")

    @dg.asset
    def u1() -> None: ...

    @dg.asset
    def u2() -> None: ...

    @dg.asset
    def u3() -> None: ...

    condition_initial = AC.on_cron("@hourly")
    # the updated condition buries the original condition in a different layer of the condition tree,
    # but we want to make sure we retain memory of the values. added conditions will not impact
    # the result of the condition (it will always be missing and never failed)
    condition_updated = (condition_initial & AC.missing()) | AC.execution_failed()

    current_time = datetime.datetime(2025, 8, 16, 8, 16, 0)

    @dg.asset(key=downstream_key, deps=[u1, u2, u3], automation_condition=condition_initial)
    def downstream_initial() -> None: ...
    @dg.asset(key=downstream_key, deps=[u1, u2, u3], automation_condition=condition_updated)
    def downstream_updated() -> None: ...

    defs_initial = dg.Definitions(assets=[u1, u2, u3, downstream_initial])
    defs_updated = dg.Definitions(assets=[u1, u2, u3, downstream_updated])

    instance = dg.DagsterInstance.ephemeral()

    # initial baseline evaluation
    result = dg.evaluate_automation_conditions(
        defs_initial, instance=instance, evaluation_time=current_time
    )
    current_time += datetime.timedelta(hours=1)  # pass a cron tick

    # simulate a scenario where we materialize each upstream one by one and then evaluate
    for i, step in enumerate(sequence):
        defs = defs_initial if step == "initial" else defs_updated
        if i in {1, 2, 3}:
            instance.report_runless_asset_event(dg.AssetMaterialization(dg.AssetKey([f"u{i}"])))
        result = dg.evaluate_automation_conditions(
            defs, instance=instance, evaluation_time=current_time, cursor=result.cursor
        )
        # after we request u3, we should request the downstream asset, but the next evaluation
        # afterwards should not request it again
        expected_requested = 1 if i == 3 else 0
        assert result.total_requested == expected_requested


def test_node_unique_id() -> None:
    condition = (
        AC.any_deps_match(AC.missing())
        .allow(AssetSelection.keys("a"))
        .ignore(AssetSelection.keys("b"))
    )
    assert (
        condition.get_node_unique_id(parent_unique_id=None, index=None, target_key=None)
        == "80f87fb32baaf7ce3f65f68c12d3eb11"
    )
    assert condition.get_backcompat_node_unique_ids(
        parent_unique_id=None, index=None, target_key=None
    ) == ["35b152923d1d99348e85c3cbe426bcb7"]


def test_since_condition_cursor_backcompat() -> None:
    # This cursor was generated on master branch after:
    # - Initial evaluation at 2025-08-16 08:16:00
    # - Advancing time by 1 hour (passing a cron tick) and evaluating
    # - Materializing u1 and evaluating
    # - Materializing u2 and evaluating
    # It represents the state where we've seen u1 and u2 materialized, but not u3 yet.
    SERIALIZED_CURSOR = '{"__class__": "AssetDaemonCursor", "evaluation_id": 4, "last_observe_request_timestamp_by_asset_key": {"__mapping_items__": []}, "previous_condition_cursors": [{"__class__": "AutomationConditionCursor", "effective_timestamp": 1755360960.0, "last_event_id": 2, "node_cursors_by_unique_id": {"3a9f75060a801f9d701f3a413d3bf357": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": true}, "extra_state": null, "metadata": {}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": false}}, "70f16bbec00eb312c4da7cfd827c0d6f": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["u2"]}, "value": true}, "extra_state": null, "metadata": {"reset_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 1}, "reset_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755360960.0}, "trigger_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 3}, "trigger_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755360960.0}}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["u2"]}, "value": true}}, "78fcf9818d90b7a754ce5ca8438f38a7": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": true}, "extra_state": null, "metadata": {"reset_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 0}, "reset_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755357360.0}, "trigger_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 1}, "trigger_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755360960.0}}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": true}}, "8cdd899bf2549b7a5c2e859374ece3e0": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["u1"]}, "value": true}, "extra_state": null, "metadata": {"reset_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 1}, "reset_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755360960.0}, "trigger_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 2}, "trigger_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755360960.0}}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["u1"]}, "value": true}}, "96cdedfb5f6eda4a495cd248e15b0199": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": true}, "extra_state": null, "metadata": {}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": true}}, "9a75684cd0cb75d2ebc6d5766664af8d": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": true}, "extra_state": "30941eb8f7bb4d6d5a93ddcb3d7d9a44", "metadata": {}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": false}}, "cb267651e07bf0097d6897293b5e0a16": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": true}, "extra_state": null, "metadata": {}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": true}}, "de921ed0f21116b1537bdad77a7c3300": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["u3"]}, "value": true}, "extra_state": null, "metadata": {"reset_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 1}, "reset_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755360960.0}, "trigger_evaluation_id": {"__class__": "IntMetadataEntryData", "value": null}, "trigger_timestamp": {"__class__": "FloatMetadataEntryData", "value": null}}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["u3"]}, "value": false}}}, "previous_requested_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": false}, "result_value_hash": "4600b054dde72ed5b654f1e698b73e0e"}], "previous_evaluation_state": []}'

    downstream_key = dg.AssetKey("downstream")

    @dg.asset
    def u1() -> None: ...

    @dg.asset
    def u2() -> None: ...

    @dg.asset
    def u3() -> None: ...

    condition = AC.on_cron("@hourly")

    @dg.asset(key=downstream_key, deps=[u1, u2, u3], automation_condition=condition)
    def downstream() -> None: ...

    defs = dg.Definitions(assets=[u1, u2, u3, downstream])
    instance = dg.DagsterInstance.ephemeral()

    # Start at the same time as when the cursor was generated (after the cron tick)
    current_time = datetime.datetime(2025, 8, 16, 8, 16, 0) + datetime.timedelta(hours=1)

    # Deserialize the cursor from the string representation
    cursor = deserialize_value(SERIALIZED_CURSOR, AssetDaemonCursor)

    # First evaluation with the deserialized cursor - nothing should be requested yet
    # because we haven't materialized u3
    result = dg.evaluate_automation_conditions(
        defs, instance=instance, evaluation_time=current_time, cursor=cursor
    )
    assert result.total_requested == 0

    # Now materialize u3 (the final parent that was missing)
    instance.report_runless_asset_event(dg.AssetMaterialization(dg.AssetKey("u3")))

    # Evaluate again - now downstream should be requested since all parents are materialized
    result = dg.evaluate_automation_conditions(
        defs, instance=instance, evaluation_time=current_time, cursor=result.cursor
    )
    assert result.total_requested == 1


def test_since_condition_cursor_forwardscompat() -> None:
    # This cursor was generated on a781e0b6fa (the commit with the new cursoring scheme) after:
    # - Initial evaluation on 2025-08-15 at 08:00
    # - Advancing time to 2025-08-16 at 08:00 (passing the daily cron tick)
    # - Materializing u1 for the 2025-08-15 partition and evaluating
    # - Materializing u2 for the 2025-08-15 partition and evaluating
    # It represents the state where 2/3 parents are materialized for the target partition,
    # but the child hasn't been requested yet (since not all deps are materialized).
    SERIALIZED_CURSOR = '{"__class__": "AssetDaemonCursor", "evaluation_id": 4, "last_observe_request_timestamp_by_asset_key": {"__mapping_items__": []}, "previous_condition_cursors": [{"__class__": "AutomationConditionCursor", "effective_timestamp": 1755356400.0, "last_event_id": 2, "node_cursors_by_unique_id": {"3a9f75060a801f9d701f3a413d3bf357": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [{"__class__": "TimeWindow", "end": {"__class__": "TimestampWithTimezone", "timestamp": 1755302400.0, "timezone": "UTC"}, "start": {"__class__": "TimestampWithTimezone", "timestamp": 1755216000.0, "timezone": "UTC"}}], "num_partitions": 1, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}, "extra_state": null, "metadata": {}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [], "num_partitions": 0, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}}, "562f40d3d07714853ad23d3b2883d133": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["u2"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [{"__class__": "TimeWindow", "end": {"__class__": "TimestampWithTimezone", "timestamp": 1755302400.0, "timezone": "UTC"}, "start": {"__class__": "TimestampWithTimezone", "timestamp": 1755216000.0, "timezone": "UTC"}}], "num_partitions": 1, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}, "extra_state": null, "metadata": {"reset_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 1}, "reset_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755356400.0}, "trigger_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 3}, "trigger_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755356400.0}}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["u2"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [{"__class__": "TimeWindow", "end": {"__class__": "TimestampWithTimezone", "timestamp": 1755302400.0, "timezone": "UTC"}, "start": {"__class__": "TimestampWithTimezone", "timestamp": 1755216000.0, "timezone": "UTC"}}], "num_partitions": 1, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}}, "7836fe11210a0648dff336a0e150ce5f": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "HistoricalAllPartitionsSubsetSentinel"}, "extra_state": "7858324293e6e919455de534a653a5ba", "metadata": {}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [], "num_partitions": 0, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}}, "96cdedfb5f6eda4a495cd248e15b0199": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [{"__class__": "TimeWindow", "end": {"__class__": "TimestampWithTimezone", "timestamp": 1755302400.0, "timezone": "UTC"}, "start": {"__class__": "TimestampWithTimezone", "timestamp": 1755216000.0, "timezone": "UTC"}}], "num_partitions": 1, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}, "extra_state": null, "metadata": {}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [{"__class__": "TimeWindow", "end": {"__class__": "TimestampWithTimezone", "timestamp": 1755302400.0, "timezone": "UTC"}, "start": {"__class__": "TimestampWithTimezone", "timestamp": 1755216000.0, "timezone": "UTC"}}], "num_partitions": 1, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}}, "ae80579d587a0ea06a04022191963990": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["u1"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [{"__class__": "TimeWindow", "end": {"__class__": "TimestampWithTimezone", "timestamp": 1755302400.0, "timezone": "UTC"}, "start": {"__class__": "TimestampWithTimezone", "timestamp": 1755216000.0, "timezone": "UTC"}}], "num_partitions": 1, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}, "extra_state": null, "metadata": {"reset_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 1}, "reset_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755356400.0}, "trigger_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 2}, "trigger_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755356400.0}}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["u1"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [{"__class__": "TimeWindow", "end": {"__class__": "TimestampWithTimezone", "timestamp": 1755302400.0, "timezone": "UTC"}, "start": {"__class__": "TimestampWithTimezone", "timestamp": 1755216000.0, "timezone": "UTC"}}], "num_partitions": 1, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}}, "b4a17490e985f92579e3325ab203b912": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [{"__class__": "TimeWindow", "end": {"__class__": "TimestampWithTimezone", "timestamp": 1755302400.0, "timezone": "UTC"}, "start": {"__class__": "TimestampWithTimezone", "timestamp": 1755216000.0, "timezone": "UTC"}}], "num_partitions": 1, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}, "extra_state": null, "metadata": {"reset_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 0}, "reset_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755270000.0}, "trigger_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 1}, "trigger_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755356400.0}}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [{"__class__": "TimeWindow", "end": {"__class__": "TimestampWithTimezone", "timestamp": 1755302400.0, "timezone": "UTC"}, "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}}], "num_partitions": 15, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}}, "c329bf0762287468ab84214435c87beb": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["u3"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [{"__class__": "TimeWindow", "end": {"__class__": "TimestampWithTimezone", "timestamp": 1755302400.0, "timezone": "UTC"}, "start": {"__class__": "TimestampWithTimezone", "timestamp": 1755216000.0, "timezone": "UTC"}}], "num_partitions": 1, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}, "extra_state": null, "metadata": {"reset_evaluation_id": {"__class__": "IntMetadataEntryData", "value": 1}, "reset_timestamp": {"__class__": "FloatMetadataEntryData", "value": 1755356400.0}, "trigger_evaluation_id": {"__class__": "IntMetadataEntryData", "value": null}, "trigger_timestamp": {"__class__": "FloatMetadataEntryData", "value": null}}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["u3"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [], "num_partitions": 0, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}}, "cb267651e07bf0097d6897293b5e0a16": {"__class__": "AutomationConditionNodeCursor", "candidate_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [{"__class__": "TimeWindow", "end": {"__class__": "TimestampWithTimezone", "timestamp": 1755302400.0, "timezone": "UTC"}, "start": {"__class__": "TimestampWithTimezone", "timestamp": 1755216000.0, "timezone": "UTC"}}], "num_partitions": 1, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}, "extra_state": null, "metadata": {}, "subsets_with_metadata": [], "true_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [{"__class__": "TimeWindow", "end": {"__class__": "TimestampWithTimezone", "timestamp": 1755302400.0, "timezone": "UTC"}, "start": {"__class__": "TimestampWithTimezone", "timestamp": 1755216000.0, "timezone": "UTC"}}], "num_partitions": 1, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}}}, "previous_requested_subset": {"__class__": "AssetSubset", "asset_key": {"__class__": "AssetKey", "path": ["downstream"]}, "value": {"__class__": "TimeWindowPartitionsSubset", "included_time_windows": [], "num_partitions": 0, "partitions_def": {"__class__": "TimeWindowPartitionsDefinition", "cron_schedule": "0 0 * * *", "end": null, "end_offset": 0, "exclusions": null, "fmt": "%Y-%m-%d", "start": {"__class__": "TimestampWithTimezone", "timestamp": 1754006400.0, "timezone": "UTC"}, "timezone": "UTC"}}}, "result_value_hash": "bf312509eca3285a8e2941599b0c0b7e"}], "previous_evaluation_state": []}'

    downstream_key = dg.AssetKey("downstream")
    partitions_def = dg.DailyPartitionsDefinition(start_date="2025-08-01")
    target_partition = "2025-08-15"

    @dg.asset(partitions_def=partitions_def)
    def u1() -> None: ...

    @dg.asset(partitions_def=partitions_def)
    def u2() -> None: ...

    @dg.asset(partitions_def=partitions_def)
    def u3() -> None: ...

    condition = AC.on_cron("@daily")

    @dg.asset(
        key=downstream_key,
        deps=[u1, u2, u3],
        automation_condition=condition,
        partitions_def=partitions_def,
    )
    def downstream() -> None: ...

    defs = dg.Definitions(assets=[u1, u2, u3, downstream])
    instance = dg.DagsterInstance.ephemeral()

    # Start at the same time as when the cursor was generated (2025-08-16 08:00)
    current_time = datetime.datetime(2025, 8, 16, 8, 0, 0)

    # Deserialize the cursor from the string representation
    cursor = dg.deserialize_value(SERIALIZED_CURSOR, AssetDaemonCursor)

    # First evaluation with the deserialized cursor - nothing should be requested yet
    # because we haven't materialized u3 for the target partition
    result = dg.evaluate_automation_conditions(
        defs, instance=instance, evaluation_time=current_time, cursor=cursor
    )
    assert result.total_requested == 0

    # Now materialize u3 for the target partition (the final parent that was missing)
    instance.report_runless_asset_event(
        dg.AssetMaterialization(dg.AssetKey("u3"), partition=target_partition)
    )

    # Evaluate again - now downstream should be requested since all parents are materialized
    result = dg.evaluate_automation_conditions(
        defs, instance=instance, evaluation_time=current_time, cursor=result.cursor
    )
    assert result.total_requested == 1
