import time

from dagster import (
    AssetKey,
    AssetOut,
    RunRequest,
    SkipReason,
    StaticPartitionsDefinition,
    asset,
    job,
    multi_asset,
    multi_asset_sensor,
    op,
)


@asset
def asset_a():
    return [1, 2, 3]


@asset
def asset_b():
    return [5, 6, 7]


@asset
def asset_c():
    return [11, 12, 13]


@asset
def asset_d():
    return [15, 16, 17]


@multi_asset(
    outs={
        "my_string_asset": AssetOut(),
        "my_int_asset": AssetOut(),
    }
)
def multi_asset_a():
    return "abc", 123


@op
def log_asset_sensor(context):
    context.log.info(context.op_config["message"])


@job
def log_asset_sensor_job():
    log_asset_sensor()


@multi_asset_sensor(
    monitored_assets=[AssetKey("asset_a"), AssetKey("asset_b")],
    job=log_asset_sensor_job,
)
def asset_a_and_b_sensor(context):
    asset_events = context.latest_materialization_records_by_key()
    if all(asset_events.values()):
        context.advance_all_cursors()
        return RunRequest(
            run_key=context.cursor,
            run_config={
                "ops": {
                    "log_asset_sensor": {"config": {"message": f"Asset events dict {asset_events}"}}
                }
            },
        )
    else:
        return None


@multi_asset_sensor(
    monitored_assets=[AssetKey("asset_c"), AssetKey("asset_d")],
    job=log_asset_sensor_job,
)
def asset_c_or_d_sensor(context):
    asset_events = context.latest_materialization_records_by_key()
    if any(asset_events.values()):
        context.advance_all_cursors()
        return RunRequest(
            run_key=context.cursor,
            run_config={
                "ops": {
                    "log_asset_sensor": {"config": {"message": f"Asset events dict {asset_events}"}}
                }
            },
        )
    else:
        return SkipReason("Condition not met")


@multi_asset_sensor(
    monitored_assets=[AssetKey("my_string_asset"), AssetKey("my_int_asset")],
    job=log_asset_sensor_job,
)
def asset_string_and_int_sensor(context):
    asset_events = context.latest_materialization_records_by_key()
    if all(asset_events.values()):
        context.advance_all_cursors()
        return RunRequest(
            run_key=context.cursor,
            run_config={
                "ops": {
                    "log_asset_sensor": {"config": {"message": f"Asset events dict {asset_events}"}}
                }
            },
        )


@multi_asset_sensor(
    monitored_assets=[AssetKey("asset_a")],
    job=log_asset_sensor_job,
)
def every_fifth_materialization_sensor(context):
    all_asset_a_events = context.materialization_records_for_key(
        asset_key=AssetKey("asset_a"), limit=5
    )

    if len(all_asset_a_events) == 5:
        context.advance_cursor({AssetKey("asset_a"): all_asset_a_events[-1]})
        return RunRequest(
            run_key=context.cursor,
            run_config={
                "ops": {
                    "log_asset_sensor": {
                        "config": {"message": f"Asset events dict {all_asset_a_events}"}
                    }
                }
            },
        )


@asset
def upstream():
    return 1


@asset
def downstream(upstream):
    return upstream + 1


@asset
def runs_long():
    time.sleep(60)
    return 1


@asset
def waits(runs_long):
    return runs_long + 1


def _build_partitioned_assets():
    assets = []

    for i in range(10):

        @asset(
            name=f"partitioned_asset_{i}",
            group_name="partitioned_assets",
            partitions_def=StaticPartitionsDefinition([str(j) for j in range(20)]),
        )
        def partitioned_asset():
            return 1

        assets.append(partitioned_asset)
    return assets


partitioned_assets = _build_partitioned_assets()


@multi_asset_sensor(
    monitored_assets=[asset_def.key for asset_def in partitioned_assets],
    job=log_asset_sensor_job,
)
def partitioned_multi_asset_sensor(context):
    run_requests = []
    for (
        partition,
        materialization_by_asset,
    ) in context.latest_materialization_records_by_partition_and_asset().items():
        context.advance_cursor(materialization_by_asset)
        run_requests.append(
            RunRequest(
                run_config={
                    "ops": {
                        "log_asset_sensor": {
                            "config": {
                                "message": (
                                    f"Materializations by asset {materialization_by_asset} for"
                                    f" partition key {partition}"
                                )
                            }
                        }
                    }
                },
            )
        )
    return run_requests


def get_asset_sensors_repo():
    return [
        asset_a,
        asset_b,
        asset_a_and_b_sensor,
        asset_c,
        asset_d,
        asset_c_or_d_sensor,
        multi_asset_a,
        asset_string_and_int_sensor,
        every_fifth_materialization_sensor,
        upstream,
        downstream,
        runs_long,
        waits,
        *partitioned_assets,
        partitioned_multi_asset_sensor,
    ]
