import dagster as dg


@dg.asset(
    # add other useful metadata
    compute_kind="javascript",
)
def my_asset(
    context: dg.AssetExecutionContext,
    pipes_subprocess_client: dg.PipesSubprocessClient,
):
    """Runs Javascript to generate an asset."""
    return pipes_subprocess_client.run(
        command=["node", "tensorflow/main.js"],
        context=context.op_execution_context,
        extras={},
    ).get_materialize_result()


defs = dg.Definitions(
    assets=[my_asset],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)