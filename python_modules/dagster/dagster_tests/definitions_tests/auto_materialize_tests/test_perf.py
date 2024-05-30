import time

from dagster import (
    DailyPartitionsDefinition,
    Definitions,
    HourlyPartitionsDefinition,
    SchedulingCondition,
)
from dagster_test.toys.auto_materializing.large_graph import AssetLayerConfig, build_assets

from dagster_tests.definitions_tests.auto_materialize_tests.test_user_space_ds_api import (
    execute_ds_ticks,
)


def test_eager_perf() -> None:
    hourly_partitions_def = HourlyPartitionsDefinition("2020-01-01-00:00")
    daily_partitions_def = DailyPartitionsDefinition("2020-01-01")
    assets = build_assets(
        id="perf_test",
        layer_configs=[
            AssetLayerConfig(100, 0, hourly_partitions_def),
            AssetLayerConfig(200, 2, hourly_partitions_def),
            AssetLayerConfig(200, 4, hourly_partitions_def),
            AssetLayerConfig(200, 4, daily_partitions_def),
            AssetLayerConfig(200, 2, daily_partitions_def),
            AssetLayerConfig(100, 2, daily_partitions_def),
        ],
        auto_materialize_policy=SchedulingCondition.eager().as_auto_materialize_policy(),
    )

    start = time.time()
    for _ in execute_ds_ticks(defs=Definitions(assets=assets), n=2):
        end = time.time()
        duration = end - start
        # all iterations should take less than 20 seconds on this graph
        assert duration < 20.0
        start = time.time()
