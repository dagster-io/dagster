import datetime

from dagster import (
    AssetSelection,
    AutomationCondition,
    AutomationConditionTester,
    Definitions,
    HourlyPartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
)


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


def test_current_time_manipulation() -> None:
    tester = AutomationConditionTester(
        defs=defs,
        asset_selection=AssetSelection.assets(hourly),
        current_time=datetime.datetime(2020, 2, 2),
    )

    result = tester.evaluate()
    assert result.total_requested == 1
    assert result.get_requested_partitions(hourly.key) == {"2020-02-01-23:00"}

    tester.set_current_time(datetime.datetime(3005, 5, 5))
    result = tester.evaluate()
    assert result.total_requested == 1
    assert result.get_requested_partitions(hourly.key) == {"3005-05-04-23:00"}

    tester.add_materializations(hourly.key, ["3005-05-03-23:00"])
    result = tester.evaluate()
    assert result.total_requested == 0
    assert result.get_requested_partitions(hourly.key) == set()
