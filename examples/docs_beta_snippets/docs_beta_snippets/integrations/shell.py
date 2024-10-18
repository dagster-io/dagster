import shutil

import dagster as dg


@dg.asset
def shell_asset(
    context: dg.AssetExecutionContext, pipes_subprocess_client: dg.PipesSubprocessClient
):
    shell_script_path = "/path/to/your/script.sh"
    return pipes_subprocess_client.run(
        command=["bash", shell_script_path],
        context=context,
    ).get_results()


defs = dg.Definitions(
    assets=[shell_asset],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)
