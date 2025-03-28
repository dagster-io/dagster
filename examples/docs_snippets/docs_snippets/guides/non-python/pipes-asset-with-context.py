import dagster as dg


@dg.asset(
    compute_kind="javascript",
)
def my_asset(
    context: dg.AssetExecutionContext,
    pipes_subprocess_client: dg.PipesSubprocessClient,
):
    """Runs Javascript to generate an asset."""
    return pipes_subprocess_client.run(
        command=["node", "tensorflow/main.js"],
        # highlight-start
        context=context,
        extras={
            "operation_name": "train_model",
            "config": {
                "path_to_data": "file://../tensorflow/data/data.csv",
                "data_config": {"hasHeaders": True},
                "path_to_model": "file://../tensorflow/model",
            },
        },
        # highlight-end
    ).get_materialize_result()


defs = dg.Definitions(
    assets=[my_asset],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)
