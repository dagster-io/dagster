import dagster as dg


@dg.definitions
def resources():
    return dg.Definitions(
        resources={"pipes_subprocess_client": dg.PipesSubprocessClient()}
    )
