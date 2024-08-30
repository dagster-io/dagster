import dagster as dg


@dg.asset(
    compute_kind="javascript",
)
def tensorflow_model(
    context: dg.AssetExecutionContext,
    pipes_subprocess_client: dg.PipesSubprocessClient,
):
    """Runs Javascript to generate an asset."""
    return pipes_subprocess_client.run(
        command=["node", "tensorflow/main.js"],
        context=context,
        extras={},
    ).get_materialize_result()


defs = dg.Definitions(
    assets=[tensorflow_model],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)
