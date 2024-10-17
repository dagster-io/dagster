from dagster import (
    AutomationCondition,
    AutomationConditionSensorDefinition,
    DailyPartitionsDefinition,
    Definitions,
    HourlyPartitionsDefinition,
)
from dagster_test.toys.auto_materializing.large_graph import AssetLayerConfig, build_assets


def get_defs(n: int) -> Definitions:
    hourly_partitions_def = HourlyPartitionsDefinition("2020-01-01-00:00")
    daily_partitions_def = DailyPartitionsDefinition("2020-01-01")
    unit = n // 10
    assets = build_assets(
        id="perf_test",
        layer_configs=[
            AssetLayerConfig(1 * unit, 0, hourly_partitions_def),
            AssetLayerConfig(2 * unit, 2, hourly_partitions_def),
            AssetLayerConfig(2 * unit, 4, hourly_partitions_def),
            AssetLayerConfig(2 * unit, 4, daily_partitions_def),
            AssetLayerConfig(2 * unit, 2, daily_partitions_def),
            AssetLayerConfig(1 * unit, 2, daily_partitions_def),
        ],
        automation_condition=AutomationCondition.eager(),
    )
    return Definitions(
        assets=assets,
        sensors=[
            AutomationConditionSensorDefinition("the_sensor", asset_selection="*", user_code=True)
        ],
    )


defs = get_defs(500)
