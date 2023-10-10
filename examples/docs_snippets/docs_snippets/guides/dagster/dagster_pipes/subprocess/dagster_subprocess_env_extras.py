import os
import shutil

from dagster import (
    AssetExecutionContext,
    Definitions,
    MaterializeResult,
    PipesSubprocessClient,
    asset,
    file_relative_path,
)


@asset
def subprocess_asset(
    context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient
) -> MaterializeResult:
    cmd = [shutil.which("python"), file_relative_path(__file__, "external_code.py")]
    return pipes_subprocess_client.run(
        command=cmd,
        context=context,
        extras={"foo": "bar"},
        env={
            "MY_ENV_VAR_IN_SUBPROCESS": os.environ["MY_ENV_VAR"],
        },
    ).get_materialize_result()


defs = Definitions(
    assets=[subprocess_asset],
    resources={"pipes_subprocess_client": PipesSubprocessClient()},
)
