# start_asset_marker
import shutil

from dagster import (
    AssetExecutionContext,
    PipesSubprocessClient,
    asset,
    file_relative_path,
)


@asset
def subprocess_asset(
    context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient
):
    cmd = [shutil.which("python"), file_relative_path(__file__, "external_code.py")]
    return pipes_subprocess_client.run(command=cmd, context=context).get_results()


# end_asset_marker

# start_definitions_marker

from dagster import Definitions

defs = Definitions(
    assets=[subprocess_asset],
    resources={"pipes_subprocess_client": PipesSubprocessClient()},
)
# end_definitions_marker
