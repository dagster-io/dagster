import datetime

import dagster as dg
import pytest
from dagster import AssetSelection, AutomationCondition
from dagster._core.definitions.assets.definition.asset_spec import AssetExecutionType
from dagster._core.instance import DagsterInstance


@dg.asset(
    partitions_def=dg.HourlyPartitionsDefinition("2020-01-01-00:00"),
    automation_condition=AutomationCondition.eager(),
)
def hourly() -> None: ...


@dg.asset(
    partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"]),
    automation_condition=AutomationCondition.on_missing(),
)
def static() -> None: ...


@dg.asset(automation_condition=AutomationCondition.eager(), deps=["upstream"])
def unpartitioned() -> None: ...


defs = dg.Definitions(assets=[hourly, static, unpartitioned])


@dg.op
def noop(): ...


observable_a = dg.AssetsDefinition(
    specs=[dg.AssetSpec("a", automation_condition=AutomationCondition.cron_tick_passed("@daily"))],
    execution_type=AssetExecutionType.OBSERVATION,
    node_def=noop,
    keys_by_output_name={"result": dg.AssetKey("a")},
)
observable_b = dg.AssetsDefinition(
    specs=[
        dg.AssetSpec(
            "b",
            deps=["a"],
            automation_condition=AutomationCondition.cron_tick_passed("@daily"),
        )
    ],
    execution_type=AssetExecutionType.OBSERVATION,
    node_def=noop,
    keys_by_output_name={"result": dg.AssetKey("b")},
)
materializable_c = dg.AssetsDefinition(
    specs=[
        dg.AssetSpec(
            "c",
            deps="b",
            automation_condition=AutomationCondition.cron_tick_passed("@daily"),
        )
    ],
    execution_type=AssetExecutionType.MATERIALIZATION,
    node_def=noop,
    keys_by_output_name={"result": dg.AssetKey("c")},
)
defs_with_observables = dg.Definitions(assets=[observable_a, observable_b, materializable_c])


def test_basic_regular_defs() -> None:
    instance = DagsterInstance.ephemeral()
    result = dg.evaluate_automation_conditions(
        defs=defs,
        asset_selection=AssetSelection.assets(unpartitioned),
        instance=instance,
    )
    assert result.total_requested == 0

    instance.report_runless_asset_event(dg.AssetMaterialization("upstream"))
    result = dg.evaluate_automation_conditions(
        defs=defs,
        asset_selection=AssetSelection.assets(unpartitioned),
        instance=instance,
        cursor=result.cursor,
    )
    assert result.total_requested == 1

    result = dg.evaluate_automation_conditions(
        defs=defs,
        asset_selection=AssetSelection.assets(unpartitioned),
        instance=instance,
        cursor=result.cursor,
    )
    assert result.total_requested == 0


def test_basic_assets_defs() -> None:
    instance = DagsterInstance.ephemeral()

    result = dg.evaluate_automation_conditions(defs=[unpartitioned], instance=instance)
    assert result.total_requested == 0

    instance.report_runless_asset_event(dg.AssetMaterialization(asset_key=dg.AssetKey("upstream")))
    result = dg.evaluate_automation_conditions(
        defs=[unpartitioned], instance=instance, cursor=result.cursor
    )
    assert result.total_requested == 1

    result = dg.evaluate_automation_conditions(
        defs=[unpartitioned], instance=instance, cursor=result.cursor
    )
    assert result.total_requested == 0


def test_observable_asset_defs() -> None:
    instance = DagsterInstance.ephemeral()

    evaluation_time = datetime.datetime(2024, 5, 5, 10, 1)
    result = dg.evaluate_automation_conditions(
        defs=defs_with_observables, instance=instance, evaluation_time=evaluation_time
    )
    # no cron tick passed
    assert result.total_requested == 0

    evaluation_time = evaluation_time + datetime.timedelta(days=1)
    result = dg.evaluate_automation_conditions(
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
        (None, dg.HourlyPartitionsDefinition("2020-01-01-00:00"), 24),
        (dg.HourlyPartitionsDefinition("2020-01-01-00:00"), None, 1),
        (
            dg.HourlyPartitionsDefinition("2020-01-01-00:00"),
            dg.HourlyPartitionsDefinition("2020-01-01-00:00"),
            24,
        ),
        (
            dg.HourlyPartitionsDefinition("2020-01-01-00:00"),
            dg.StaticPartitionsDefinition(
                ["2019-01-02-00:00", "2019-01-03-00:00", "2019-01-04-00:00"]
            ),
            0,
        ),
        (
            dg.HourlyPartitionsDefinition("2020-01-01-00:00"),
            dg.StaticPartitionsDefinition(
                ["2020-01-01-01:00", "2020-01-01-04:00", "2020-01-01-08:00"]
            ),
            3,
        ),
        (
            dg.HourlyPartitionsDefinition("2020-01-01-00:00"),
            dg.StaticPartitionsDefinition(["2019-01-01-08:00", "a", "2020-01-01-16:00"]),
            1,
        ),
        (
            dg.HourlyPartitionsDefinition("2020-01-01-00:00"),
            dg.StaticPartitionsDefinition(["a", "b", "c"]),
            0,
        ),
        (
            dg.StaticPartitionsDefinition(["a", "b", "c"]),
            dg.StaticPartitionsDefinition(["a", "b", "c"]),
            3,
        ),
    ],
)
def test_asset_matches(a_partitions_def, b_partitions_def, expected_requested) -> None:
    # default: a -> b
    def _get_asset_defs(b_upstream: bool = False, no_deps: bool = False) -> dg.Definitions:
        if no_deps:
            a_deps = None
            b_deps = None
        elif b_upstream:
            a_deps = ["b"]
            b_deps = None
        else:
            a_deps = None
            b_deps = ["a"]

        @dg.asset(
            deps=a_deps,
            partitions_def=a_partitions_def,
        )
        def a() -> None: ...

        @dg.asset(
            deps=b_deps,
            partitions_def=b_partitions_def,
            auto_materialize_policy=AutomationCondition.asset_matches(
                dg.AssetKey("a"), AutomationCondition.missing()
            ).as_auto_materialize_policy(),
        )
        def b() -> None: ...

        return dg.Definitions(assets=[a, b])

    evaluation_time = datetime.datetime(2020, 1, 2)

    for asset_defs in [
        _get_asset_defs(),
        _get_asset_defs(b_upstream=True),
        _get_asset_defs(no_deps=True),
    ]:
        instance = DagsterInstance.ephemeral()

        result = dg.evaluate_automation_conditions(
            defs=asset_defs,
            instance=instance,
            evaluation_time=evaluation_time,
        )
        assert result.total_requested == expected_requested

        # if a is unpartitioned, test when a is materialized
        if a_partitions_def is None:
            instance.report_runless_asset_event(dg.AssetMaterialization("a"))
            result = dg.evaluate_automation_conditions(
                defs=asset_defs,
                instance=instance,
                cursor=result.cursor,
                evaluation_time=evaluation_time,
            )
            assert result.total_requested == 0
