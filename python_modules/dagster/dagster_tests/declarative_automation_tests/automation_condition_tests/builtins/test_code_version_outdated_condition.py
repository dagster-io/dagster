import datetime

import dagster as dg
from dagster._core.definitions.data_version import CODE_VERSION_TAG, DATA_VERSION_TAG


def test_code_version_outdated_condition_tracks_latest_materialization_provenance() -> None:
    condition = dg.AutomationCondition.code_version_outdated()

    @dg.asset(name="A", code_version="old", automation_condition=condition)
    def asset_old() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    current_time = datetime.datetime(2024, 1, 1, 0, 0, 0)

    instance.report_runless_asset_event(
        dg.AssetMaterialization(
            "A", tags={CODE_VERSION_TAG: "old", DATA_VERSION_TAG: "data-version-old"}
        )
    )

    result = dg.evaluate_automation_conditions(
        defs=[asset_old], instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    @dg.asset(name="A", code_version="new", automation_condition=condition)
    def asset_new() -> None: ...

    current_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[asset_new], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 1

    instance.report_runless_asset_event(
        dg.AssetMaterialization(
            "A", tags={CODE_VERSION_TAG: "old", DATA_VERSION_TAG: "data-version-old-2"}
        )
    )
    current_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[asset_new], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 1

    instance.report_runless_asset_event(
        dg.AssetMaterialization(
            "A", tags={CODE_VERSION_TAG: "new", DATA_VERSION_TAG: "data-version-new"}
        )
    )
    current_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[asset_new], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 0


def test_code_version_outdated_condition_is_false_without_prior_provenance() -> None:
    condition = dg.AutomationCondition.code_version_outdated()

    @dg.asset(code_version="new", automation_condition=condition)
    def asset_without_materialization() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    result = dg.evaluate_automation_conditions(
        defs=[asset_without_materialization], instance=instance
    )
    assert result.total_requested == 0


def test_code_version_outdated_condition_partitioned_per_partition() -> None:
    condition = dg.AutomationCondition.code_version_outdated()
    partitions_def = dg.StaticPartitionsDefinition(["1", "2"])

    @dg.asset(
        name="partitioned_asset",
        code_version="old",
        automation_condition=condition,
        partitions_def=partitions_def,
    )
    def asset_old() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    current_time = datetime.datetime(2024, 1, 1, 0, 0, 0)

    for partition_key in ["1", "2"]:
        instance.report_runless_asset_event(
            dg.AssetMaterialization(
                "partitioned_asset",
                partition=partition_key,
                tags={CODE_VERSION_TAG: "old", DATA_VERSION_TAG: f"old-{partition_key}"},
            )
        )

    result = dg.evaluate_automation_conditions(
        defs=[asset_old], instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    @dg.asset(
        name="partitioned_asset",
        code_version="new",
        automation_condition=condition,
        partitions_def=partitions_def,
    )
    def asset_new() -> None: ...

    current_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[asset_new], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 2

    instance.report_runless_asset_event(
        dg.AssetMaterialization(
            "partitioned_asset",
            partition="1",
            tags={CODE_VERSION_TAG: "new", DATA_VERSION_TAG: "new-1"},
        )
    )
    current_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[asset_new], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 1
