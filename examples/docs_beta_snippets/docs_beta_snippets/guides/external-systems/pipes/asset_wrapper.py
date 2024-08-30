import shutil

import dagster as dg


@dg.asset
def wrapper_asset(
    context: dg.AssetExecutionContext, pipes_subprocess_client: dg.PipesSubprocessClient
) -> None:
    external_python_code_path = "/usr/bin/external_code.py"
    return pipes_subprocess_client.run(
        command=[shutil.which("python"), external_python_code_path],
        context=context,
    ).get_results()


defs = dg.Definitions(
    assets=[wrapper_asset],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)
