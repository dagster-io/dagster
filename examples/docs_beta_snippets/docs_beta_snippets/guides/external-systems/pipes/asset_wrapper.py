import shutil

import dagster as dg


@dg.asset
def wrapper_asset(
    context: dg.AssetExecutionContext, pipes_subprocess_client: dg.PipesSubprocessClient
) -> None:
    return pipes_subprocess_client.run(
        command=[
            shutil.which("python"),
            dg.file_relative_path(__file__, "external_code.py"),
        ],
        context=context,
    ).get_results()


defs = dg.Definitions(
    assets=[wrapper_asset],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)
