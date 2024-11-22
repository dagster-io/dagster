AWS_CREDENTIALS = {}

# start_client
from dagster_k8s import PipesK8sClient

eks_client = PipesK8sClient(
    # The client will have automatic access to all
    # environment variables in the execution context.
    env={**AWS_CREDENTIALS, "AWS_REGION": "us-west-2"},
    kubeconfig_file="path/to/kubeconfig",
    kube_context="my-eks-cluster",
)
# end_client

# start_asset
from dagster import AssetExecutionContext, asset

container_cfg = {
    "name": "hello-world-pod",
    "image": "bash:latest",
    "command": ["bash", "-cx"],
    "args": ['echo "Hello World!"'],
}


@asset
def execute_hello_world_task(context: AssetExecutionContext):
    return eks_client.run(
        context=context,
        base_pod_meta={"name": "hello-world-pod"},
        base_pod_spec={"containers": [container_cfg]},
    ).get_results()


# end_asset
