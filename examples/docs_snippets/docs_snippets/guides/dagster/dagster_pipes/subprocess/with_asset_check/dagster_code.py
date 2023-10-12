import shutil

from dagster import (
    AssetExecutionContext,
    Definitions,
    MaterializeResult,
    PipesSubprocessClient,
    asset,
    asset_check,
    file_relative_path,
    AssetExecutionContext,
    AssetCheckResult
)


@asset
def my_asset():
    ...


@asset_check(asset="my_asset")
def no_empty_order_check(
    context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient
) -> AssetCheckResult:
    cmd = [
        shutil.which("python"),
        file_relative_path(__file__, "external_code.py"),
    ]
    return pipes_subprocess_client.run(
        command=cmd, context=context
    ).get_asset_check_result()


defs = Definitions(
    assets=[my_asset],
    asset_checks=[no_empty_order_check],
    resources={"pipes_subprocess_client": PipesSubprocessClient()},
)
