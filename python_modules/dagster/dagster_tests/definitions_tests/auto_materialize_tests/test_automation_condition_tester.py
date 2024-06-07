from dagster import (
    AssetSelection,
    AutomationCondition,
    Definitions,
    HourlyPartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
    evaluate_automation_conditions,
)
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
