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

from dagster import Definitions

defs = Definitions(
    assets=[subprocess_asset],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)
# end_definitions_marker
