# start_asset_marker
import shutil

import dagster as dg


@dg.asset
def subprocess_asset(
    context: dg.AssetExecutionContext, pipes_subprocess_client: dg.PipesSubprocessClient
) -> dg.MaterializeResult:
    cmd = [shutil.which("python"), dg.file_relative_path(__file__, "external_code.py")]
    return pipes_subprocess_client.run(
        command=cmd, context=context
    ).get_materialize_result()


# end_asset_marker


# start_definitions_marker
@dg.definitions
def resources():
    return dg.Definitions(
        resources={"pipes_subprocess_client": dg.PipesSubprocessClient()}
    )


# end_definitions_marker
