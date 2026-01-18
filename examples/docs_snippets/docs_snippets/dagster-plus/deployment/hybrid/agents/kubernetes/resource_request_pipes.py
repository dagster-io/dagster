from dagster_k8s import PipesK8sClient

import dagster as dg


@dg.asset
def k8s_pod_asset(
    context: dg.AssetExecutionContext,
    pipes_k8s_client: PipesK8sClient,
) -> dg.MaterializeResult:
    # The kubernetes pod spec for the computation we want to run
    # with resource limits and requests set.
    pod_spec = {
        "containers": [
            {
                "name": "pipes-example",
                "image": "your-image-uri",
                "resources": {
                    "requests": {
                        "memory": "64Mi",
                        "cpu": "250m",
                    },
                    "limits": {
                        "memory": "128Mi",
                        "cpu": "500m",
                    },
                },
            },
        ]
    }
    return pipes_k8s_client.run(
        context=context,
        namespace="your-namespace",
        base_pod_spec=pod_spec,
    ).get_materialize_result()
