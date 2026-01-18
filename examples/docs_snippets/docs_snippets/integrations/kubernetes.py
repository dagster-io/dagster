from dagster_k8s import PipesK8sClient

import dagster as dg


@dg.asset
def k8s_pipes_asset(
    context: dg.AssetExecutionContext, k8s_pipes_client: PipesK8sClient
):
    return k8s_pipes_client.run(
        context=context,
        image="pipes-example:v1",
    ).get_materialize_result()


defs = dg.Definitions(
    assets=[k8s_pipes_asset],
    resources={
        "k8s_pipes_client": PipesK8sClient(),
    },
)
