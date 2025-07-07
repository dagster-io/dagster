from typing import Optional

import dagster as dg
import pytest
from dagster import AutomationCondition, DagsterInstance
from dagster._core.definitions.data_version import DATA_VERSION_TAG


@pytest.mark.parametrize(
    "partitions_def",
    [
        None,
        dg.DailyPartitionsDefinition("2025-01-01"),
        dg.StaticPartitionsDefinition(["0", "1", "2"]),
    ],
)
def test_data_version_changed_condition(partitions_def: Optional[dg.PartitionsDefinition]) -> None:
    partition_key = partitions_def.get_last_partition_key() if partitions_def else None

    @dg.asset(automation_condition=AutomationCondition.data_version_changed())
    def foo() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    defs = dg.Definitions(assets=[foo])
    instance = DagsterInstance.ephemeral()

    # hasn't newly updated
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # now updates
    instance.report_runless_asset_event(
        dg.AssetMaterialization(foo.key, tags={DATA_VERSION_TAG: "a"}, partition=partition_key)
    )
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # no longer "newly updated"
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # now updates with the same data version
    instance.report_runless_asset_event(
        dg.AssetMaterialization(foo.key, tags={DATA_VERSION_TAG: "a"}, partition=partition_key)
    )
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # again
    instance.report_runless_asset_event(
        dg.AssetMaterialization(foo.key, tags={DATA_VERSION_TAG: "a"}, partition=partition_key)
    )
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # new data version
    instance.report_runless_asset_event(
        dg.AssetMaterialization(foo.key, tags={DATA_VERSION_TAG: "b"}, partition=partition_key)
    )
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # new data version
    instance.report_runless_asset_event(
        dg.AssetMaterialization(foo.key, tags={DATA_VERSION_TAG: "c"}, partition=partition_key)
    )
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # no longer "newly updated"
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0
