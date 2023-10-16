from dagster import (
    AssetExecutionContext,
    AssetKey,
    DailyPartitionsDefinition,
    EventLogEntry,
    RunRequest,
    SensorEvaluationContext,
    asset,
    asset_check,
    asset_sensor,
    define_asset_job,
)
from dagster_k8s import PipesK8sClient
from dagster_pipes import encode_env_var

pod_spec_for_kind = {
    "containers": [
        {
            "imagePullPolicy": "Never",
        }
    ]
}


@asset(
    key="telem_post_processing",
    deps=[
        AssetKey(["static", "admin_boundaries"]),
        AssetKey(["s3", "joined_sensor_telem"]),
    ],
    group_name="pipes",
    partitions_def=DailyPartitionsDefinition("2023-10-01"),
)
def telem_post_processing(context: AssetExecutionContext, k8s_pipes_client: PipesK8sClient):
    return k8s_pipes_client.run(
        context=context,
        namespace="default",
        image="pipes-materialize:latest",
        env={"DAGSTER_PIPES_IS_DAGSTER_PIPED_PROCESS": encode_env_var(True)},
        base_pod_spec=pod_spec_for_kind,
    ).get_materialize_result()


@asset_check(asset="telem_post_processing")
def telem_post_processing_check(context: AssetExecutionContext, k8s_pipes_client: PipesK8sClient):
    return k8s_pipes_client.run(
        context=context,
        namespace="default",
        image="pipes-check:latest",
        env={"DAGSTER_PIPES_IS_DAGSTER_PIPED_PROCESS": encode_env_var(True)},
        base_pod_spec=pod_spec_for_kind,
    ).get_asset_check_result()


telem_post_processing_job = define_asset_job(
    name="telem_post_processing_job", selection="telem_post_processing"
)


@asset_sensor(asset_key=AssetKey(["s3", "joined_sensor_telem"]), job=telem_post_processing_job)
def telem_post_processing_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    return RunRequest(
        run_key=context.cursor,
        run_config={},
    )
