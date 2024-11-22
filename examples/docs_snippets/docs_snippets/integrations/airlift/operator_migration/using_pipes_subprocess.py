from dagster import AssetExecutionContext, PipesSubprocessClient, asset


@asset
def script_result(context: AssetExecutionContext):
    return (
        PipesSubprocessClient()
        .run(context=context, command="python /path/to/script.py")
        .get_results()
    )
