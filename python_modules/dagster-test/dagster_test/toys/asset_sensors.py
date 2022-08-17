from dagster import (
    AssetKey,
    AssetOut,
    RunRequest,
    SkipReason,
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
    asset_keys=[AssetKey("asset_a"), AssetKey("asset_b")],
    job=log_asset_sensor_job,
)
def asset_a_and_b_sensor(context, asset_events):
    asset_events = context.get_latest_event([AssetKey("asset_a"), AssetKey("asset_b")])
    if all(asset_events.values()):
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
    asset_keys=[AssetKey("asset_c"), AssetKey("asset_d")],
    job=log_asset_sensor_job,
)
def asset_c_or_d_sensor(context):
    asset_events = context.get_latest_event([AssetKey("asset_c"), AssetKey("asset_d")])
    if any(asset_events.values()):
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
    asset_keys=[AssetKey("my_string_asset"), AssetKey("my_int_asset")],
    job=log_asset_sensor_job,
)
def asset_string_and_int_sensor(context):
    asset_events = context.get_latest_event([AssetKey("my_string_asset"), AssetKey("my_int_asset")])
    if all(asset_events.values()):
        return RunRequest(
            run_key=context.cursor,
            run_config={
                "ops": {
                    "log_asset_sensor": {"config": {"message": f"Asset events dict {asset_events}"}}
                }
            },
        )


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
    ]
