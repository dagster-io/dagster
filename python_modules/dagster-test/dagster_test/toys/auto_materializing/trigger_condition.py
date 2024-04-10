from dagster import AssetCondition, AssetKey, AutoMaterializePolicy, Definitions, asset
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

# should really be all_parents_newer, but that doesn't exist yet
condition = AssetCondition.parent_newer() & AssetCondition.trigger_newer(trigger=s3_trigger.key)
policy = AutoMaterializePolicy.from_asset_condition(condition)


@asset(
    # has to have a different policy because it technically has no parents so its parents will
    # never be newer (dumb, but wouldn't be an issue if we had an all_parents_newer condition)
    auto_materialize_policy=AutoMaterializePolicy.from_asset_condition(
        AssetCondition.trigger_newer(trigger=s3_trigger.key)
    )
)
def a():
    return 1


@asset(auto_materialize_policy=policy)
def b(a):
    return a + 1


@asset(auto_materialize_policy=policy)
def c(a):
    return a + 1


@asset(auto_materialize_policy=policy)
def d(b, c):
    return b + c


defs = Definitions(
    assets=[a, b, c, d],
    triggers=[s3_trigger],
)
