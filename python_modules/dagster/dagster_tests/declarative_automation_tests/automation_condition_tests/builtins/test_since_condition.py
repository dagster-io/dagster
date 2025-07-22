import datetime

import dagster as dg
import pytest
from dagster._core.definitions.declarative_automation.operators import SinceCondition
from dagster._core.definitions.declarative_automation.operators.since_operator import (
    SinceConditionData,
)
from dagster._core.definitions.events import AssetKeyPartitionKey

from dagster_tests.declarative_automation_tests.automation_condition_tests.builtins.test_dep_condition import (
    get_hardcoded_condition,
)
from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import one_asset


@pytest.mark.asyncio
async def test_since_condition_unpartitioned() -> None:
    primary_condition, true_set_primary = get_hardcoded_condition()
    reference_condition, true_set_reference = get_hardcoded_condition()

    condition = SinceCondition(
        trigger_condition=primary_condition, reset_condition=reference_condition
    )
    state = AutomationConditionScenarioState(one_asset, automation_condition=condition)

    # nothing true
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # primary becomes true, but reference has never been true
    true_set_primary.add(AssetKeyPartitionKey(dg.AssetKey("A")))
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1
    true_set_primary.remove(AssetKeyPartitionKey(dg.AssetKey("A")))

    # reference becomes true, and it's after primary
    true_set_reference.add(AssetKeyPartitionKey(dg.AssetKey("A")))
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0
    true_set_reference.remove(AssetKeyPartitionKey(dg.AssetKey("A")))

    # primary becomes true again, and it's since reference has become true
    true_set_primary.add(AssetKeyPartitionKey(dg.AssetKey("A")))
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1
    true_set_primary.remove(AssetKeyPartitionKey(dg.AssetKey("A")))

    # remains true on the neprimaryt evaluation
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1

    # primary becomes true again, still doesn't change anything
    true_set_primary.add(AssetKeyPartitionKey(dg.AssetKey("A")))
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1
    true_set_primary.remove(AssetKeyPartitionKey(dg.AssetKey("A")))

    # now reference becomes true again
    true_set_reference.add(AssetKeyPartitionKey(dg.AssetKey("A")))
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0
    true_set_reference.remove(AssetKeyPartitionKey(dg.AssetKey("A")))

    # remains false on the neprimaryt evaluation
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0


def test_since_condition() -> None:
    # this is a duplication of the test above, but written in the new style,
    # and with additional metadata tests. we're retaining the above test in
    # this PR to prove that nothing changed
    trigger_condition, true_set_trigger = get_hardcoded_condition()
    reset_condition, true_set_reset = get_hardcoded_condition()
    condition = trigger_condition.since(reset_condition)
    apk = AssetKeyPartitionKey(dg.AssetKey("a"))

    @dg.asset(automation_condition=condition)
    def a(): ...

    instance = dg.DagsterInstance.ephemeral()

    # nothing happened yet
    evaluation_time = datetime.datetime(2024, 1, 1)
    result = dg.evaluate_automation_conditions(
        defs=[a], instance=instance, evaluation_time=evaluation_time
    )
    assert result.total_requested == 0
    assert SinceConditionData.from_metadata(
        result.results[0].serializable_evaluation.metadata
    ) == SinceConditionData(
        trigger_evaluation_id=None,
        trigger_timestamp=None,
        reset_evaluation_id=None,
        reset_timestamp=None,
    )

    # trigger condition is true, and reset condition is not
    true_set_trigger.add(apk)
    evaluation_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[a], instance=instance, cursor=result.cursor, evaluation_time=evaluation_time
    )
    true_set_trigger.remove(apk)
    assert result.total_requested == 1
    trigger_timestamp = evaluation_time.timestamp()
    assert SinceConditionData.from_metadata(
        result.results[0].serializable_evaluation.metadata
    ) == SinceConditionData(
        trigger_evaluation_id=1,
        trigger_timestamp=trigger_timestamp,
        reset_evaluation_id=None,
        reset_timestamp=None,
    )

    # reset condition is true, and trigger condition is not
    true_set_reset.add(apk)
    evaluation_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[a], instance=instance, cursor=result.cursor, evaluation_time=evaluation_time
    )
    true_set_reset.remove(apk)
    assert result.total_requested == 0
    reset_timestamp = evaluation_time.timestamp()
    assert SinceConditionData.from_metadata(
        result.results[0].serializable_evaluation.metadata
    ) == SinceConditionData(
        trigger_evaluation_id=1,
        trigger_timestamp=trigger_timestamp,
        reset_evaluation_id=2,
        reset_timestamp=reset_timestamp,
    )

    # trigger condition becomes true again
    true_set_trigger.add(apk)
    evaluation_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[a], instance=instance, cursor=result.cursor, evaluation_time=evaluation_time
    )
    true_set_trigger.remove(apk)
    assert result.total_requested == 1
    trigger_timestamp = evaluation_time.timestamp()
    assert SinceConditionData.from_metadata(
        result.results[0].serializable_evaluation.metadata
    ) == SinceConditionData(
        trigger_evaluation_id=3,
        trigger_timestamp=trigger_timestamp,
        reset_evaluation_id=2,
        reset_timestamp=reset_timestamp,
    )

    # everything remains the same on the next evaluation
    evaluation_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[a], instance=instance, cursor=result.cursor, evaluation_time=evaluation_time
    )
    assert result.total_requested == 1
    assert SinceConditionData.from_metadata(
        result.results[0].serializable_evaluation.metadata
    ) == SinceConditionData(
        trigger_evaluation_id=3,
        trigger_timestamp=trigger_timestamp,
        reset_evaluation_id=2,
        reset_timestamp=reset_timestamp,
    )

    # primary becomes true again, doesn't change the result, but does update metadata
    true_set_trigger.add(apk)
    evaluation_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[a], instance=instance, cursor=result.cursor, evaluation_time=evaluation_time
    )
    true_set_trigger.remove(apk)
    assert result.total_requested == 1
    trigger_timestamp = evaluation_time.timestamp()
    assert SinceConditionData.from_metadata(
        result.results[0].serializable_evaluation.metadata
    ) == SinceConditionData(
        trigger_evaluation_id=5,
        trigger_timestamp=trigger_timestamp,
        reset_evaluation_id=2,
        reset_timestamp=reset_timestamp,
    )

    # reset condition becomes true again
    true_set_reset.add(apk)
    evaluation_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[a], instance=instance, cursor=result.cursor, evaluation_time=evaluation_time
    )
    true_set_reset.remove(apk)
    assert result.total_requested == 0
    reset_timestamp = evaluation_time.timestamp()
    assert SinceConditionData.from_metadata(
        result.results[0].serializable_evaluation.metadata
    ) == SinceConditionData(
        trigger_evaluation_id=5,
        trigger_timestamp=trigger_timestamp,
        reset_evaluation_id=6,
        reset_timestamp=reset_timestamp,
    )

    # everything remains the same on the next evaluation
    evaluation_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[a], instance=instance, cursor=result.cursor, evaluation_time=evaluation_time
    )
    assert result.total_requested == 0
    assert SinceConditionData.from_metadata(
        result.results[0].serializable_evaluation.metadata
    ) == SinceConditionData(
        trigger_evaluation_id=5,
        trigger_timestamp=trigger_timestamp,
        reset_evaluation_id=6,
        reset_timestamp=reset_timestamp,
    )

    # both become true again, all metadata updated
    true_set_trigger.add(apk)
    true_set_reset.add(apk)
    evaluation_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[a], instance=instance, cursor=result.cursor, evaluation_time=evaluation_time
    )
    assert result.total_requested == 0
    timestamp = evaluation_time.timestamp()
    assert SinceConditionData.from_metadata(
        result.results[0].serializable_evaluation.metadata
    ) == SinceConditionData(
        trigger_evaluation_id=8,
        trigger_timestamp=timestamp,
        reset_evaluation_id=8,
        reset_timestamp=timestamp,
    )


def test_allow_ignore() -> None:
    selection = dg.AssetSelection.groups("a")
    a = dg.AutomationCondition.any_deps_updated()
    b = dg.AutomationCondition.any_deps_in_progress()
    initial = a.since(b)

    assert initial.allow(selection) == a.allow(selection).since(b.allow(selection))
    assert initial.ignore(selection) == a.ignore(selection).since(b.ignore(selection))
