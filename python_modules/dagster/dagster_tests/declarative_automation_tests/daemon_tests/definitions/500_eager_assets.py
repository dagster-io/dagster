import dagster as dg
from dagster import AutomationCondition
from dagster_test.toys.auto_materializing.large_graph import AssetLayerConfig, build_assets


def get_defs(n: int) -> dg.Definitions:
    hourly_partitions_def = dg.HourlyPartitionsDefinition("2020-01-01-00:00")
    daily_partitions_def = dg.DailyPartitionsDefinition("2020-01-01")
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
    return dg.Definitions(
        assets=assets,
        sensors=[
            dg.AutomationConditionSensorDefinition(
                "the_sensor", target="*", use_user_code_server=True
            )
        ],
    )


defs = get_defs(500)
