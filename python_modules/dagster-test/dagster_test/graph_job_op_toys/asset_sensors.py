from dagster import (
    AssetKey,
    DagsterEventType,
    Out,
    RunRequest,
    asset,
    asset_status_sensor,
    job,
    multi_asset,
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
        "my_string_asset": Out(),
        "my_int_asset": Out(),
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


@asset_status_sensor(
    asset_keys=[AssetKey("asset_a"), AssetKey("asset_b")],
    asset_status=DagsterEventType.ASSET_MATERIALIZATION,
    job=log_asset_sensor_job,
)
def asset_a_and_b_sensor(context, asset_events):
    return RunRequest(
        run_key=context.cursor,
        run_config={
            "ops": {
                "log_asset_sensor": {"config": {"message": f"Asset events dict {asset_events}"}}
            }
        },
    )


@asset_status_sensor(
    asset_keys=[AssetKey("asset_c"), AssetKey("asset_d")],
    asset_status=DagsterEventType.ASSET_MATERIALIZATION,
    trigger_fn=lambda x: any(x.values()),
    job=log_asset_sensor_job,
)
def asset_c_or_d_sensor(context, asset_events):
    return RunRequest(
        run_key=context.cursor,
        run_config={
            "ops": {
                "log_asset_sensor": {"config": {"message": f"Asset events dict {asset_events}"}}
            }
        },
    )


@asset_status_sensor(
    asset_keys=[AssetKey("my_string_asset"), AssetKey("my_int_asset")],
    asset_status=DagsterEventType.ASSET_MATERIALIZATION,
    job=log_asset_sensor_job,
)
def asset_string_and_int_sensor(context, asset_events):
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
