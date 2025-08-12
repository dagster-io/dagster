import datetime
import operator

import dagster as dg
import pytest
from dagster import AutoMaterializePolicy, AutomationCondition
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.declarative_automation.operators import (
    AndAutomationCondition,
    OrAutomationCondition,
)
from dagster._core.definitions.declarative_automation.serialized_objects import (
    HistoricalAllPartitionsSubsetSentinel,
)
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.subset.key_ranges import KeyRangesPartitionsSubset
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster_shared.check import CheckError

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.base_scenario import run_request
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    daily_partitions_def,
    day_partition_key,
    one_asset,
    time_partitions_start_datetime,
)


@pytest.mark.asyncio
async def test_missing_unpartitioned() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.missing()
    )

    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1
    original_value_hash = result.value_hash

    # still true
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1
    assert result.value_hash == original_value_hash

    # after a run of A it's now False
    state, result = await state.with_runs(run_request("A")).evaluate("A")
    assert result.true_subset.size == 0
    assert result.value_hash != original_value_hash

    # if we evaluate from scratch, it's also False
    _, result = await state.without_cursor().evaluate("A")
    assert result.true_subset.size == 0


@pytest.mark.asyncio
async def test_missing_time_partitioned() -> None:
    state = (
        AutomationConditionScenarioState(
            one_asset, automation_condition=AutomationCondition.missing()
        )
        .with_asset_properties(partitions_def=daily_partitions_def)
        .with_current_time(time_partitions_start_datetime)
        .with_current_time_advanced(days=6, minutes=1)
    )

    state, result = await state.evaluate("A")
    assert result.true_subset.size == 6

    # still true
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 6

    # after two runs of A those partitions are now False
    state, result = await state.with_runs(
        run_request("A", day_partition_key(time_partitions_start_datetime, 1)),
        run_request("A", day_partition_key(time_partitions_start_datetime, 3)),
    ).evaluate("A")
    assert result.true_subset.size == 4

    # if we evaluate from scratch, they're still False
    _, result = await state.without_cursor().evaluate("A")
    assert result.true_subset.size == 4


def test_serialize_definitions_with_asset_condition() -> None:
    amp = AutoMaterializePolicy.from_automation_condition(
        AutomationCondition.eager()
        & ~AutomationCondition.newly_updated().since(
            AutomationCondition.cron_tick_passed(cron_schedule="0 * * * *", cron_timezone="UTC")
        )
    )

    @dg.asset(auto_materialize_policy=amp)
    def my_asset() -> int:
        return 0

    serialized = dg.serialize_value(amp)
    assert isinstance(serialized, str)

    serialized = dg.serialize_value(
        RepositorySnap.from_def(dg.Definitions(assets=[my_asset]).get_repository_def())
    )
    assert isinstance(serialized, str)


def test_serialize_definitions_with_user_code_asset_condition() -> None:
    class MyAutomationCondition(dg.AutomationCondition):
        def evaluate(self, context: AutomationContext) -> dg.AutomationResult:
            return dg.AutomationResult(
                context, context.asset_graph_view.get_full_subset(key=context.key)
            )

    automation_condition = AutomationCondition.eager() | MyAutomationCondition()

    @dg.asset(automation_condition=automation_condition)
    def my_asset() -> int:
        return 0

    serialized = dg.serialize_value(
        RepositorySnap.from_def(dg.Definitions(assets=[my_asset]).get_repository_def())
    )
    assert isinstance(serialized, str)
    deserialized = dg.deserialize_value(serialized)
    assert isinstance(deserialized, RepositorySnap)
    external_assets = deserialized.asset_nodes
    assert len(external_assets) == 1
    automation_condition = external_assets[0].automation_condition
    # it does not make its way onto the ExternalAssetNode
    assert automation_condition is None


def test_deserialize_definitions_with_asset_condition() -> None:
    serialized = """{"__class__": "AutoMaterializePolicy", "asset_condition": {"__class__": "AndAssetCondition", "operands": [{"__class__": "RuleCondition", "rule": {"__class__": "MaterializeOnParentUpdatedRule", "updated_parent_filter": null}}, {"__class__": "NotAssetCondition", "operand": {"__class__": "NotAssetCondition", "operand": {"__class__": "RuleCondition", "rule": {"__class__": "MaterializeOnCronRule", "all_partitions": false, "cron_schedule": "0 * * * *", "timezone": "UTC"}}}}]}, "max_materializations_per_minute": null, "rules": {"__frozenset__": []}, "time_window_partition_scope_minutes": 1e-06}"""

    deserialized = dg.deserialize_value(serialized, dg.AutoMaterializePolicy)
    assert isinstance(deserialized, dg.AutoMaterializePolicy)


def test_label_automation_condition() -> None:
    not_missing = (~AutomationCondition.missing()).with_label("Not missing")
    not_in_progress = (~AutomationCondition.in_progress()).with_label("Not in progress")
    not_missing_and_not_in_progress = (not_missing & not_in_progress).with_label("Blah")
    assert not_missing_and_not_in_progress.label == "Blah"
    assert not_missing_and_not_in_progress.get_node_snapshot("").label == "Blah"
    assert not_missing_and_not_in_progress.children[0].get_label() == "Not missing"
    assert not_missing_and_not_in_progress.children[1].get_label() == "Not in progress"


def test_without_automation_condition() -> None:
    a = AutomationCondition.in_latest_time_window()
    b = AutomationCondition.any_deps_match(AutomationCondition.in_progress())
    c = ~AutomationCondition.any_deps_in_progress()

    orig = a & b & c

    # simple cases
    assert orig.without(a) == b & c
    assert orig.without(b) == a & c
    assert orig.without(c) == a & b

    # ensure works if using different instances of the same operands
    assert orig.without(AutomationCondition.in_latest_time_window()) == b & c
    assert orig.without(~AutomationCondition.any_deps_in_progress()) == a & b

    # ensure label is preserved
    assert orig.with_label("my_label").without(a) == (b & c).with_label("my_label")

    # make sure it errors if an invalid condition is passed
    with pytest.raises(CheckError, match="Condition not found"):
        orig.without(AutomationCondition.in_progress())

    with pytest.raises(CheckError, match="Condition not found"):
        orig.without(
            AutomationCondition.any_deps_match(
                AutomationCondition.in_progress() | AutomationCondition.missing()
            )
        )

    with pytest.raises(CheckError, match="Condition not found"):
        orig.without(
            AutomationCondition.in_latest_time_window(lookback_delta=datetime.timedelta(hours=3))
        )

    with pytest.raises(CheckError, match="fewer than 2 operands"):
        orig.without(a).without(b)


def test_replace_automation_conditions() -> None:
    a = AutomationCondition.in_latest_time_window().with_label("in_latest_time_window")
    b = AutomationCondition.any_deps_match(AutomationCondition.in_progress())
    c = (~AutomationCondition.any_deps_in_progress()).with_label("not_any_deps_in_progress")
    d = AutomationCondition.missing()

    orig = a & b | c

    assert orig.replace(a, d) == d & b | c
    assert orig.replace(
        AutomationCondition.in_progress(), d
    ) == a & AutomationCondition.any_deps_match(d) | (
        ~AutomationCondition.any_deps_match(d).with_label("any_deps_in_progress")
    ).with_label("not_any_deps_in_progress")
    assert orig.replace("not_any_deps_in_progress", d) == a & b | d
    assert orig.replace("any_deps_in_progress", d) == a & b | (~d).with_label(
        "not_any_deps_in_progress"
    )


def test_replace_automation_condition_by_names() -> None:
    a = AutomationCondition.in_latest_time_window()
    b = AutomationCondition.missing()
    c = AutomationCondition.any_deps_match(AutomationCondition.in_progress())

    assert (a & b).replace("missing", c) == a & c


def test_replace_automation_condition_since() -> None:
    a = AutomationCondition.in_latest_time_window().with_label("in_latest_time_window")
    b = AutomationCondition.any_deps_match(AutomationCondition.in_progress())
    c = (~AutomationCondition.any_deps_in_progress()).with_label("not_any_deps_in_progress")
    d = AutomationCondition.missing()

    orig = a.since(b | c)

    assert orig.replace(a, d) == d.since(b | c)
    assert orig.replace(b, d) == a.since(d | c)
    assert orig.replace("not_any_deps_in_progress", d) == a.since(b | d)

    assert AutomationCondition.eager() != AutomationCondition.eager().replace(
        "handled", AutomationCondition.newly_updated()
    )


def test_replace_automation_condition_with_label() -> None:
    a = (
        AutomationCondition.eager()
        .replace("newly_updated", AutomationCondition.data_version_changed())
        .with_label("eager_respecting_data_version")
    )
    assert a.get_label() == "eager_respecting_data_version"


@pytest.mark.parametrize("method", ["allow", "ignore"])
def test_filter_automation_condition(method: str) -> None:
    a = AutomationCondition.in_latest_time_window()
    b = AutomationCondition.any_deps_match(AutomationCondition.in_progress())
    c = ~AutomationCondition.any_deps_in_progress()

    orig = a & b | c

    # simple case
    apply_filter = operator.methodcaller(method, AssetSelection.keys("A"))
    assert apply_filter(orig) == a & apply_filter(b) | apply_filter(c)

    # propagate to children
    complex_condition = orig & orig | orig
    assert apply_filter(complex_condition) == (
        (a & apply_filter(b) | apply_filter(c)) & (a & apply_filter(b) | apply_filter(c))
        | (a & apply_filter(b) | apply_filter(c))
    )


@pytest.mark.parametrize(
    ("op", "cond"), [(operator.and_, AndAutomationCondition), (operator.or_, OrAutomationCondition)]
)
def test_consolidate_automation_conditions(op, cond) -> None:
    not_missing = ~AutomationCondition.missing()
    not_in_progress = ~AutomationCondition.in_progress()
    not_missing_not_in_progress = op(not_missing, not_in_progress)
    in_latest_time_window = AutomationCondition.in_latest_time_window()
    not_any_deps_in_progress = ~AutomationCondition.any_deps_in_progress()
    in_latest_time_window_not_any_deps_in_progress = op(
        in_latest_time_window, not_any_deps_in_progress
    )

    assert op(not_missing_not_in_progress, in_latest_time_window_not_any_deps_in_progress) == (
        cond(
            operands=[
                not_missing,
                not_in_progress,
                in_latest_time_window,
                not_any_deps_in_progress,
            ]
        )
    )

    assert op(not_missing_not_in_progress, in_latest_time_window) == (
        cond(
            operands=[
                not_missing,
                not_in_progress,
                in_latest_time_window,
            ]
        )
    )

    second_labeled_automation_condition = in_latest_time_window_not_any_deps_in_progress.with_label(
        "in_latest_time_window_not_any_deps_in_progress"
    )
    assert op(not_missing_not_in_progress, second_labeled_automation_condition) == (
        cond(
            operands=[
                not_missing,
                not_in_progress,
                second_labeled_automation_condition,
            ]
        )
    )

    assert op(not_missing, in_latest_time_window_not_any_deps_in_progress) == (
        cond(
            operands=[
                not_missing,
                in_latest_time_window,
                not_any_deps_in_progress,
            ]
        )
    )

    first_labeled_automation_condition = not_missing_not_in_progress.with_label(
        "not_missing_not_in_progress"
    )
    assert op(
        first_labeled_automation_condition, in_latest_time_window_not_any_deps_in_progress
    ) == (
        cond(
            operands=[
                first_labeled_automation_condition,
                in_latest_time_window,
                not_any_deps_in_progress,
            ]
        )
    )

    assert op(first_labeled_automation_condition, second_labeled_automation_condition) == (
        cond(
            operands=[
                first_labeled_automation_condition,
                second_labeled_automation_condition,
            ]
        )
    )


def test_use_historical_all_partitions_subset_sentinel() -> None:
    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"]))
    def A(): ...

    @dg.asset(
        deps=[A],
        automation_condition=~dg.AutomationCondition.any_deps_match(
            dg.AutomationCondition.missing()
        ),
    )
    def B(): ...

    defs = dg.Definitions(assets=[A, B])
    instance = dg.DagsterInstance.ephemeral()
    result = dg.evaluate_automation_conditions(
        defs=defs, instance=instance, evaluation_time=datetime.datetime(2024, 8, 16, 4, 35)
    )
    assert result.total_requested == 0
    assert isinstance(
        result.results[0]
        .child_results[0]
        .child_results[0]
        .child_results[0]
        .serializable_evaluation.candidate_subset,
        HistoricalAllPartitionsSubsetSentinel,
    )


def test_use_key_ranges_partitions_subset() -> None:
    @dg.asset(
        partitions_def=dg.DynamicPartitionsDefinition(name="some_def"),
        # using this weird condition to make a predictable non-AllPartitionsSubset candidate subset
        automation_condition=dg.AutomationCondition.missing() & dg.AutomationCondition.missing(),
    )
    def A(): ...

    defs = dg.Definitions(assets=[A])
    instance = dg.DagsterInstance.ephemeral()
    instance.add_dynamic_partitions("some_def", ["a", "b", "c", "d", "e"])
    for partition in ["a", "c", "e"]:
        instance.report_runless_asset_event(
            dg.AssetMaterialization(asset_key=dg.AssetKey("A"), partition=partition)
        )

    current_time = datetime.datetime(2024, 8, 16, 4, 35)
    result = dg.evaluate_automation_conditions(
        defs=defs, instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 2

    with partition_loading_context(effective_dt=current_time, dynamic_partitions_store=instance):
        # outer AND condition
        serializable_evaluation = result.results[0].serializable_evaluation
        assert isinstance(serializable_evaluation.true_subset.value, KeyRangesPartitionsSubset)
        assert serializable_evaluation.true_subset.value.get_partition_keys() == ["b", "d"]

        assert isinstance(
            serializable_evaluation.candidate_subset, HistoricalAllPartitionsSubsetSentinel
        )

        # inner missing condition (second operand)
        serializable_evaluation = result.results[0].child_results[1].serializable_evaluation
        assert isinstance(serializable_evaluation.true_subset.value, KeyRangesPartitionsSubset)
        assert serializable_evaluation.true_subset.value.get_partition_keys() == ["b", "d"]

        assert isinstance(serializable_evaluation.candidate_subset, SerializableEntitySubset)
        assert isinstance(serializable_evaluation.candidate_subset.value, KeyRangesPartitionsSubset)
        assert serializable_evaluation.candidate_subset.value.get_partition_keys() == ["b", "d"]
