@asset
def telem_post_processing(
    context: AssetExecutionContext,
    k8s_pipes_client: PipesK8sClient,
) -> MaterializeResult:
    return k8s_pipes_client.run(
        context=context,
        image="pipes-materialize:latest",
        base_pod_spec=pod_spec_for_kind,
    ).get_materialize_result()
