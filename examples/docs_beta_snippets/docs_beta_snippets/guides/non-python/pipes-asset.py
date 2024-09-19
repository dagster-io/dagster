import dagster as dg


@dg.asset(
    # Set compute type metadata
    compute_kind="javascript",
)
def tensorflow_model(
    context: dg.AssetExecutionContext,
    # Attaches the PipesSubprocessClient as a resource
    pipes_subprocess_client: dg.PipesSubprocessClient,
):
    # Run the script using Node
    return pipes_subprocess_client.run(
        command=["node", "tensorflow/main.js"],
        context=context,
        extras={},
    ).get_materialize_result()


# Define the Dagster Definitions object
defs = dg.Definitions(
    assets=[tensorflow_model],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)
