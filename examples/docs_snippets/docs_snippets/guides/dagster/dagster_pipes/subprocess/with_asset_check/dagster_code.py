import shutil

import dagster as dg


@dg.asset
def my_asset(): ...


@dg.asset_check(asset="my_asset")
def no_empty_order_check(
    context: dg.AssetCheckExecutionContext,
    pipes_subprocess_client: dg.PipesSubprocessClient,
) -> dg.AssetCheckResult:
    cmd = [
        shutil.which("python"),
        dg.file_relative_path(__file__, "external_code.py"),
    ]
    return pipes_subprocess_client.run(
        command=cmd, context=context.op_execution_context
    ).get_asset_check_result()


defs = dg.Definitions(
    assets=[my_asset],
    asset_checks=[no_empty_order_check],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)
