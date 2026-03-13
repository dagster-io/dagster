"""Tests for event timestamp support in automation conditions.

Validates:
- TimedSubsetAutomationCondition stores timing metadata on AutomationResult
- CronTickPassedCondition produces per-partition timestamps
- NewlyUpdatedCondition produces per-partition timestamps
- SinceCondition uses TimingMetadata for precise trigger/reset resolution
- Fallback behavior when timestamps are unavailable
"""

import datetime

import dagster as dg
from dagster import AutomationCondition
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._utils.env import environ

from dagster_tests.declarative_automation_tests.automation_condition_tests.builtins.test_dep_condition import (
    get_hardcoded_condition,
)


def test_cron_tick_passed_returns_timestamp() -> None:
    """CronTickPassedCondition should produce timing metadata (not serialized to subsets_with_metadata)."""
    condition = AutomationCondition.cron_tick_passed(cron_schedule="0 * * * *", cron_timezone="UTC")

    @dg.asset(automation_condition=condition)
    def A() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    current_time = datetime.datetime(2020, 2, 2, 0, 55)

    # baseline - no cron tick passed yet
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # cron tick passes — asset should be requested
    current_time = datetime.datetime(2020, 2, 2, 1, 5)
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 1


def test_newly_updated_returns_timestamp_unpartitioned() -> None:
    """NewlyUpdatedCondition should produce timing metadata (not serialized to subsets_with_metadata)."""
    condition = AutomationCondition.newly_updated()

    @dg.asset(automation_condition=condition)
    def A() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    current_time = datetime.datetime(2020, 2, 2, 0, 55)

    # baseline
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # materialize A — should be detected as newly updated
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    current_time += datetime.timedelta(minutes=5)
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 1


def test_since_condition_timestamp_resolution_unpartitioned() -> None:
    """When both trigger and reset fire on the same tick, timestamps determine the winner.

    CronTickPassed returns the cron tick time, NewlyUpdated returns the materialization time.
    Since the materialization happens after the cron tick, trigger should win.
    """
    condition = AutomationCondition.newly_updated().since(
        AutomationCondition.cron_tick_passed(cron_schedule="0 * * * *", cron_timezone="UTC")
    )

    @dg.asset(automation_condition=condition)
    def A() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    current_time = datetime.datetime(2020, 2, 2, 0, 55)

    # baseline
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # Materialize A, then the cron tick passes — both fire in the same eval.
    # The materialization event timestamp will be from the real clock (recent),
    # while the cron tick timestamp is 2020-02-02T01:00:00. Since the
    # materialization timestamp is after the cron tick, trigger wins.
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    current_time += datetime.timedelta(minutes=10)
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 1

    # Next cron tick without a new materialization — reset wins
    current_time += datetime.timedelta(hours=1)
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 0


def test_since_condition_timestamp_resolution_partitioned() -> None:
    """Per-partition timestamp resolution: when one partition is updated in the same
    eval as a cron tick, only that partition should remain in true_subset.
    """
    condition = AutomationCondition.newly_updated().since(
        AutomationCondition.cron_tick_passed(cron_schedule="0 * * * *", cron_timezone="UTC")
    )
    partitions_def = dg.StaticPartitionsDefinition(["1", "2"])

    @dg.asset(automation_condition=condition, partitions_def=partitions_def)
    def A() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    current_time = datetime.datetime(2020, 2, 2, 0, 55)

    # baseline
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # Update partition "1" and cron tick passes in the same eval
    instance.report_runless_asset_event(dg.AssetMaterialization("A", partition="1"))
    current_time += datetime.timedelta(minutes=10)
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    # Partition "1" was updated after the cron tick — trigger wins for "1"
    assert result.total_requested == 1


def test_many_partitions_uses_tick_timestamp() -> None:
    """When partition count exceeds the threshold, timing metadata should use the
    current tick timestamp for the entire subset rather than being None.

    This ensures SinceCondition still has timing data for trigger/reset resolution
    even when per-partition event timestamps are too expensive to fetch.
    """
    with environ({"DAGSTER_MAX_PARTITIONS_FOR_DA_TIMESTAMP_FETCH": "2"}):
        condition = AutomationCondition.newly_updated().since(
            AutomationCondition.cron_tick_passed(cron_schedule="0 * * * *", cron_timezone="UTC")
        )
        partitions_def = dg.StaticPartitionsDefinition(["1", "2", "3"])

        @dg.asset(automation_condition=condition, partitions_def=partitions_def)
        def A() -> None: ...

        instance = dg.DagsterInstance.ephemeral()
        current_time = datetime.datetime(2020, 2, 2, 0, 55)

        # baseline
        result = dg.evaluate_automation_conditions(
            defs=[A], instance=instance, evaluation_time=current_time
        )
        assert result.total_requested == 0

        # Update all 3 partitions (above threshold of 2), then cron tick passes.
        # With tick-timestamp fallback, trigger gets the evaluation time (1:05)
        # which is after the cron tick time (1:00), so trigger wins for all partitions.
        for pk in ["1", "2", "3"]:
            instance.report_runless_asset_event(dg.AssetMaterialization("A", partition=pk))
        current_time += datetime.timedelta(minutes=10)
        result = dg.evaluate_automation_conditions(
            defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
        )
        assert result.total_requested == 3


def test_since_condition_fallback_without_timestamps() -> None:
    """Without timestamps (e.g. HardcodedCondition), when both trigger and reset
    fire simultaneously, reset should win (conservative default).
    """
    trigger_condition, true_set_trigger = get_hardcoded_condition()
    reset_condition, true_set_reset = get_hardcoded_condition()
    condition = trigger_condition.since(reset_condition)
    apk = AssetKeyPartitionKey(dg.AssetKey("a"))

    @dg.asset(automation_condition=condition)
    def a(): ...

    instance = dg.DagsterInstance.ephemeral()
    evaluation_time = datetime.datetime(2024, 1, 1)

    # baseline
    result = dg.evaluate_automation_conditions(
        defs=[a], instance=instance, evaluation_time=evaluation_time
    )
    assert result.total_requested == 0

    # both trigger and reset fire — no timestamps, so reset wins
    true_set_trigger.add(apk)
    true_set_reset.add(apk)
    evaluation_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[a], instance=instance, cursor=result.cursor, evaluation_time=evaluation_time
    )
    assert result.total_requested == 0


def test_any_deps_match_propagates_timing_metadata() -> None:
    """any_deps_match(newly_updated) should propagate child timing metadata."""
    condition = AutomationCondition.any_deps_match(AutomationCondition.newly_updated())

    @dg.asset
    def A() -> None: ...

    @dg.asset(deps=[A], automation_condition=condition)
    def B() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    current_time = datetime.datetime(2020, 2, 2, 0, 55)

    # baseline
    result = dg.evaluate_automation_conditions(
        defs=[A, B], instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # materialize A — B should detect it via any_deps_match
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    current_time += datetime.timedelta(minutes=5)
    result = dg.evaluate_automation_conditions(
        defs=[A, B], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 1


def test_since_any_deps_updated_uses_timestamps() -> None:
    """SINCE(any_deps_updated, cron_tick_passed) should use timestamps to resolve
    simultaneous trigger and reset on the same tick.
    """
    condition = AutomationCondition.any_deps_match(AutomationCondition.newly_updated()).since(
        AutomationCondition.cron_tick_passed(cron_schedule="0 * * * *", cron_timezone="UTC")
    )

    @dg.asset
    def A() -> None: ...

    @dg.asset(deps=[A], automation_condition=condition)
    def B() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    current_time = datetime.datetime(2020, 2, 2, 0, 55)

    # baseline
    result = dg.evaluate_automation_conditions(
        defs=[A, B], instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # Materialize dep A, then cron tick passes — both fire in same eval.
    # The materialization timestamp (real clock) is after the cron tick (2020-02-02T01:00),
    # so trigger should win via timestamp resolution.
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    current_time += datetime.timedelta(minutes=10)
    result = dg.evaluate_automation_conditions(
        defs=[A, B], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 1

    # Next cron tick without new materialization — reset wins
    current_time += datetime.timedelta(hours=1)
    result = dg.evaluate_automation_conditions(
        defs=[A, B], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 0
