from dagster import (
    AssetCheckResult,
    AssetExecutionContext,
    AssetKey,
    EventLogEntry,
    RunRequest,
    SensorEvaluationContext,
    asset,
    asset_check,
    asset_sensor,
    define_asset_job,
)
from dagster_k8s import PipesK8sClient


@asset(
    key="telem_post_processing",
    deps=[
        AssetKey(["static", "admin_boundaries"]),
        AssetKey(["s3", "joined_sensor_telem"]),
    ],
    group_name="pipes",
)
def telem_post_processing(context: AssetExecutionContext, k8s_pipes_client: PipesK8sClient):
    yield from k8s_pipes_client.run(
        context=context,
        namespace="default",
        image="pipes-materialize:latest",
        base_pod_spec={
            "containers": [
                {
                    "imagePullPolicy": "Never",
                }
            ]
        },
    ).get_results()


@asset_check(asset="telem_post_processing")
def telem_post_processing_check(context, k8s_pipes_client: PipesK8sClient):
    context.log.info(context)
    values = yield from k8s_pipes_client.run(
        context=context,
        namespace="default",
        image="pipes-check:latest",
        base_pod_spec={
            "containers": [
                {
                    "imagePullPolicy": "Never",
                }
            ]
        },
    ).get_results()
    context.log.info(values)
    return AssetCheckResult(passed=True)


telem_post_processing_job = define_asset_job(
    name="telem_post_processing_job", selection="telem_post_processing"
)


@asset_sensor(asset_key=AssetKey(["s3", "joined_sensor_telem"]), job=telem_post_processing_job)
def telem_post_processing_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    return RunRequest(
        run_key=context.cursor,
        run_config={},
    )
