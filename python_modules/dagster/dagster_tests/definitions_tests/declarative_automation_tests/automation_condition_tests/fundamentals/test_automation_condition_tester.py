import datetime

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
from dagster._core.instance import DagsterInstance


@asset(
    partitions_def=HourlyPartitionsDefinition("2020-01-01-00:00"),
    auto_materialize_policy=AutomationCondition.eager().as_auto_materialize_policy(),
)
def hourly() -> None: ...


@asset(
    partitions_def=StaticPartitionsDefinition(["a", "b", "c"]),
    auto_materialize_policy=AutomationCondition.eager().as_auto_materialize_policy(),
)
def static() -> None: ...


@asset(
    auto_materialize_policy=AutomationCondition.eager().as_auto_materialize_policy(),
)
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
