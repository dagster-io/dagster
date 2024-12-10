from dagster_k8s import PipesK8sClient

from dagster import AssetExecutionContext, asset

container_cfg = {
    "name": "hello-world-pod",
    "image": "bash:latest",
    "command": ["bash", "-cx"],
    "args": ['echo "Hello World!"'],
}


@asset
def execute_hello_world_task(context: AssetExecutionContext):
    return (
        PipesK8sClient()
        .run(
            context=context,
            base_pod_meta={"name": "hello-world-pod"},
            base_pod_spec={"containers": [container_cfg]},
        )
        .get_results()
    )
