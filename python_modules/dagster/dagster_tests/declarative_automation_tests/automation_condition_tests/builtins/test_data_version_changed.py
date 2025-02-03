from typing import Optional

import pytest
from dagster import (
    AssetCheckResult,
    AssetMaterialization,
    AutomationCondition,
    DagsterInstance,
    DailyPartitionsDefinition,
    Definitions,
    PartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
    evaluate_automation_conditions,
)
from dagster._core.definitions.data_version import DATA_VERSION_TAG


@pytest.mark.parametrize("require_data_version_update", [True, False])
@pytest.mark.parametrize(
    "partitions_def",
    [None, DailyPartitionsDefinition("2025-01-01"), StaticPartitionsDefinition(["0", "1", "2"])],
)
def test_data_version_changed_condition(
    require_data_version_update: bool, partitions_def: Optional[PartitionsDefinition]
) -> None:
    partition_key = partitions_def.get_last_partition_key() if partitions_def else None

    @asset(automation_condition=AutomationCondition.data_version_changed())
    def foo() -> AssetCheckResult:
        return AssetCheckResult(passed=True)

    defs = Definitions(assets=[foo])
    instance = DagsterInstance.ephemeral()

    # hasn't newly updated
    result = evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # now updates
    instance.report_runless_asset_event(
        AssetMaterialization(foo.key, tags={DATA_VERSION_TAG: "a"}, partition=partition_key)
    )
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # no longer "newly updated"
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # now updates with the same data version
    instance.report_runless_asset_event(
        AssetMaterialization(foo.key, tags={DATA_VERSION_TAG: "a"}, partition=partition_key)
    )
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0 if require_data_version_update else 1

    # again
    instance.report_runless_asset_event(
        AssetMaterialization(foo.key, tags={DATA_VERSION_TAG: "a"}, partition=partition_key)
    )
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0 if require_data_version_update else 1

    # new data version
    instance.report_runless_asset_event(
        AssetMaterialization(foo.key, tags={DATA_VERSION_TAG: "b"}, partition=partition_key)
    )
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # new data version
    instance.report_runless_asset_event(
        AssetMaterialization(foo.key, tags={DATA_VERSION_TAG: "c"}, partition=partition_key)
    )
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # no longer "newly updated"
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0
