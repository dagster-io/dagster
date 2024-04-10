from dagster import AssetKey, AutoMaterializePolicy, Definitions, asset
from dagster._core.definitions.sensor_definition import SensorEvaluationContext
from dagster._core.definitions.trigger_definition import TriggerDefinition, TriggerResult


def has_new_s3_data(context: SensorEvaluationContext):
    cursor = int(context.cursor) if context.cursor else 0
    return TriggerResult(
        is_updated=cursor == 1,
        cursor=str((cursor + 1) % 5),
    )


s3_trigger = TriggerDefinition(
    key=AssetKey("s3_trigger"),
    # cron_schedule="*/5 * * * *",
    minimum_interval_seconds=60,
    evaluation_fn=has_new_s3_data,
)


@asset(auto_materialize_policy=AutoMaterializePolicy.eager(), deps=[s3_trigger])
def a():
    return 1


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def b(a):
    return a + 1


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def c(a):
    return a + 1


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def d(b, c):
    return b + c


defs = Definitions(assets=[a, b, c, d])
