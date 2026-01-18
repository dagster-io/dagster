import dagster_k8s as dg_k8s

import dagster as dg

container_cfg = {
    "name": "hello-world-pod",
    "image": "bash:latest",
    "command": ["bash", "-cx"],
    "args": ['echo "Hello World!"'],
}


@dg.asset
def execute_hello_world_task(context: dg.AssetExecutionContext):
    return (
        dg_k8s.PipesK8sClient()
        .run(
            context=context,
            base_pod_meta={"name": "hello-world-pod"},
            base_pod_spec={"containers": [container_cfg]},
        )
        .get_results()
    )
