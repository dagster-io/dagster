import dagster as dg


@dg.asset
def script_result(context: dg.AssetExecutionContext):
    return (
        dg.PipesSubprocessClient()
        .run(context=context, command="python /path/to/script.py")
        .get_results()
    )
