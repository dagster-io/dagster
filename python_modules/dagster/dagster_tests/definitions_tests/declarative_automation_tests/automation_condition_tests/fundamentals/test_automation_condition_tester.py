import datetime

import pytest
from dagster import (
    AssetsDefinition,
    AssetSelection,
    AssetSpec,
    AutomationCondition,
    Definitions,
    HourlyPartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
    evaluate_automation_conditions,
    op,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetExecutionType
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.instance import DagsterInstance


@asset(
    partitions_def=HourlyPartitionsDefinition("2020-01-01-00:00"),
    automation_condition=AutomationCondition.eager(),
)
def hourly() -> None: ...


@asset(
    partitions_def=StaticPartitionsDefinition(["a", "b", "c"]),
    automation_condition=AutomationCondition.on_missing(),
)
def static() -> None: ...


@asset(automation_condition=AutomationCondition.eager(), deps=["upstream"])
def unpartitioned() -> None: ...


defs = Definitions(assets=[hourly, static, unpartitioned])


@op
def noop(): ...


observable_a = AssetsDefinition(
    specs=[AssetSpec("a", automation_condition=AutomationCondition.cron_tick_passed("@daily"))],
    execution_type=AssetExecutionType.OBSERVATION,
    node_def=noop,
    keys_by_output_name={"result": AssetKey("a")},
)
observable_b = AssetsDefinition(
    specs=[
        AssetSpec(
            "b",
            deps=["a"],
            automation_condition=AutomationCondition.cron_tick_passed("@daily"),
        )
    ],
    execution_type=AssetExecutionType.OBSERVATION,
    node_def=noop,
    keys_by_output_name={"result": AssetKey("b")},
)
materializable_c = AssetsDefinition(
    specs=[
        AssetSpec(
            "c",
            deps="b",
            automation_condition=AutomationCondition.cron_tick_passed("@daily"),
        )
    ],
    execution_type=AssetExecutionType.MATERIALIZATION,
    node_def=noop,
    keys_by_output_name={"result": AssetKey("c")},
)
defs_with_observables = Definitions(assets=[observable_a, observable_b, materializable_c])


def test_basic_regular_defs() -> None:
    instance = DagsterInstance.ephemeral()
    result = evaluate_automation_conditions(
        defs=defs,
        asset_selection=AssetSelection.assets(unpartitioned),
        instance=instance,
    )
    assert result.total_requested == 0

    instance.report_runless_asset_event(AssetMaterialization("upstream"))
    result = evaluate_automation_conditions(
        defs=defs,
        asset_selection=AssetSelection.assets(unpartitioned),
        instance=instance,
        cursor=result.cursor,
    )
    assert result.total_requested == 1

    result = evaluate_automation_conditions(
        defs=defs,
        asset_selection=AssetSelection.assets(unpartitioned),
        instance=instance,
        cursor=result.cursor,
    )
    assert result.total_requested == 0


def test_basic_assets_defs() -> None:
    instance = DagsterInstance.ephemeral()

    result = evaluate_automation_conditions(defs=[unpartitioned], instance=instance)
    assert result.total_requested == 0

    instance.report_runless_asset_event(AssetMaterialization(asset_key=AssetKey("upstream")))
    result = evaluate_automation_conditions(
        defs=[unpartitioned], instance=instance, cursor=result.cursor
    )
    assert result.total_requested == 1

    result = evaluate_automation_conditions(
        defs=[unpartitioned], instance=instance, cursor=result.cursor
    )
    assert result.total_requested == 0


def test_observable_asset_defs() -> None:
    instance = DagsterInstance.ephemeral()

    evaluation_time = datetime.datetime(2024, 5, 5, 10, 1)
    result = evaluate_automation_conditions(
        defs=defs_with_observables, instance=instance, evaluation_time=evaluation_time
    )
    # no cron tick passed
    assert result.total_requested == 0

    evaluation_time = evaluation_time + datetime.timedelta(days=1)
    result = evaluate_automation_conditions(
        defs=defs_with_observables,
        instance=instance,
        cursor=result.cursor,
        evaluation_time=evaluation_time,
    )
    assert result.total_requested == 3


@pytest.mark.parametrize(
    ("a_partitions_def", "b_partitions_def", "expected_requested"),
    [
        (None, None, 1),
        (None, HourlyPartitionsDefinition("2020-01-01-00:00"), 24),
        (HourlyPartitionsDefinition("2020-01-01-00:00"), None, 1),
        (
            HourlyPartitionsDefinition("2020-01-01-00:00"),
            HourlyPartitionsDefinition("2020-01-01-00:00"),
            24,
        ),
        (
            HourlyPartitionsDefinition("2020-01-01-00:00"),
            StaticPartitionsDefinition(["a", "b", "c"]),
            0,
        ),
        (
            StaticPartitionsDefinition(["a", "b", "c"]),
            StaticPartitionsDefinition(["a", "b", "c"]),
            3,
        ),
    ],
)
def test_asset_matches(a_partitions_def, b_partitions_def, expected_requested) -> None:
    # default: a -> b
    def _get_asset_defs(b_upstream: bool = False, no_deps: bool = False) -> Definitions:
        if no_deps:
            a_deps = None
            b_deps = None
        elif b_upstream:
            a_deps = ["b"]
            b_deps = None
        else:
            a_deps = None
            b_deps = ["a"]

        @asset(
            deps=a_deps,
            partitions_def=a_partitions_def,
        )
        def a() -> None: ...

        @asset(
            deps=b_deps,
            partitions_def=b_partitions_def,
            auto_materialize_policy=AutomationCondition.asset_matches(
                AssetKey("a"), AutomationCondition.missing()
            ).as_auto_materialize_policy(),
        )
        def b() -> None: ...

        return Definitions(assets=[a, b])

    evaluation_time = datetime.datetime(2020, 1, 2)

    for asset_defs in [
        _get_asset_defs(),
        _get_asset_defs(b_upstream=True),
        _get_asset_defs(no_deps=True),
    ]:
        instance = DagsterInstance.ephemeral()

        result = evaluate_automation_conditions(
            defs=asset_defs,
            instance=instance,
            evaluation_time=evaluation_time,
        )
        assert result.total_requested == expected_requested

        # if a is unpartitioned, test when a is materialized
        if a_partitions_def is None:
            instance.report_runless_asset_event(AssetMaterialization("a"))
            result = evaluate_automation_conditions(
                defs=asset_defs,
                instance=instance,
                cursor=result.cursor,
                evaluation_time=evaluation_time,
            )
            assert result.total_requested == 0
