import os

import kubernetes
from dagster import (
    AssetKey,
    EventLogEntry,
    RunRequest,
    SensorEvaluationContext,
    asset,
    asset_sensor,
    define_asset_job,
)
from dagster_k8s import PipesK8sClient

config_file = os.path.expanduser("~/.kube/config")


@asset(
    key=AssetKey(["cdn", "scrubbed_logs"]),
    deps=[AssetKey(["cdn", "processed_logs"])],
    group_name="pipes",
)
def scrubbed_cdn_logs(context):
    kubernetes.config.load_kube_config(config_file)  # type: ignore
    client = PipesK8sClient()
    yield from client.run(
        context=context,
        namespace="default",
        image="pipes-dogfood:latest",
        base_pod_spec={
            "containers": [
                {
                    "imagePullPolicy": "Never",
                }
            ]
        },
    ).get_results()


cdn_asset_job = define_asset_job(
    name="cdn_asset_job", selection=[AssetKey(["cdn", "scrubbed-cdn-logs"])]
)


@asset_sensor(asset_key=AssetKey(["cdn", "processed_logs"]), job=cdn_asset_job)
def cdn_logs_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    return RunRequest(
        run_key=context.cursor,
        run_config={},
    )
