from dagster import AssetExecutionContext, Definitions, ExecuteInProcessResult, asset
from dagster_pipes import PipesContext

from .in_process_client import InProcessPipesClient


def execute_asset_through_def(assets_def, resources) -> ExecuteInProcessResult:
    return (
        Definitions(assets=[assets_def], resources={"inprocess_client": InProcessPipesClient()})
        .get_implicit_global_asset_job_def()
        .execute_in_process()
    )


def test_basic_materialization() -> None:
    called = {}

    def _impl(context: PipesContext):
        context.report_asset_materialization(metadata={"some_key": "some_value"})
        called["yes"] = True

    @asset
    def an_asset(context: AssetExecutionContext, inprocess_client: InProcessPipesClient):
        return inprocess_client.run(context=context, fn=_impl).get_results()

    result = execute_asset_through_def(
        an_asset, resources={"inprocess_client": InProcessPipesClient()}
    )
    assert result.success
    assert called["yes"]
