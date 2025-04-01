from dagster import RunRequest, SkipReason, asset, job


@job
def my_job():
    pass


from dagster import Config


class ReadMaterializationConfig(Config):
    asset_key: list[str]


# start_asset_sensor_marker
import dagster as dg


@dg.asset_sensor(asset_key=dg.AssetKey("my_table"), job=my_job)
def my_asset_sensor(context: dg.SensorEvaluationContext, asset_event: dg.EventLogEntry):
    assert asset_event.dagster_event and asset_event.dagster_event.asset_key
    yield RunRequest(
        run_key=context.cursor,
        run_config=dg.RunConfig(
            ops={
                "read_materialization": ReadMaterializationConfig(
                    asset_key=list(asset_event.dagster_event.asset_key.path)
                )
            }
        ),
    )


# end_asset_sensor_marker

# start_asset_sensor_test_marker
from dagster import DagsterInstance, build_sensor_context, materialize


def test_my_asset_sensor():
    @asset
    def my_table():
        return 1

    instance = DagsterInstance.ephemeral()
    ctx = build_sensor_context(instance)

    result = list(my_asset_sensor(ctx))
    assert len(result) == 1
    assert isinstance(result[0], SkipReason)

    materialize([my_table], instance=instance)

    result = list(my_asset_sensor(ctx))
    assert len(result) == 1
    assert isinstance(result[0], RunRequest)


# end_asset_sensor_test_marker
