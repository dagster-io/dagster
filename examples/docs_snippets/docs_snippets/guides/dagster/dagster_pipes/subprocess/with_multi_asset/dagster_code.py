import shutil

import dagster as dg


@dg.multi_asset(specs=[dg.AssetSpec("orders"), dg.AssetSpec("users")])
def subprocess_asset(
    context: dg.AssetExecutionContext, pipes_subprocess_client: dg.PipesSubprocessClient
):
    cmd = [
        shutil.which("python"),
        dg.file_relative_path(__file__, "external_code.py"),
    ]
    return pipes_subprocess_client.run(command=cmd, context=context).get_results()
