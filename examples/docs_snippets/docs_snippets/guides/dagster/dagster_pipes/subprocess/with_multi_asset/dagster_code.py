import shutil

from dagster import (
    AssetSpec,
    Definitions,
    AssetExecutionContext,
    PipesSubprocessClient,
    multi_asset,
    file_relative_path,
)


@multi_asset(specs=[AssetSpec("orders"), AssetSpec("users")])
def subprocess_asset(
    context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient
):
    cmd = [
        shutil.which("python"),
        file_relative_path(__file__, "external_code.py"),
    ]
    return pipes_subprocess_client.run(command=cmd, context=context).get_results()


defs = Definitions(
    assets=[subprocess_asset],
    resources={"pipes_subprocess_client": PipesSubprocessClient()},
)
