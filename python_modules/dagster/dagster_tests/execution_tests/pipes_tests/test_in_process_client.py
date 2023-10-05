from re import M
from dagster import AssetExecutionContext, Definitions, ExecuteInProcessResult, asset
from dagster._core.definitions.result import MaterializeResult
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
    mat_events = result.get_asset_materialization_events()
    assert len(mat_events) ==1
    assert mat_events[0].materialization.metadata["some_key"].value == "some_value"
    assert called["yes"]



def test_get_materialize_result():
    called = {}

    def _impl(context: PipesContext):
        context.report_asset_materialization(metadata={"some_key": "some_value"})
        called["yes"] = True

    @asset
    def an_asset(context: AssetExecutionContext, inprocess_client: InProcessPipesClient) -> MaterializeResult:
        return inprocess_client.run(context=context, fn=_impl).get_materialize_result()

    result = execute_asset_through_def(
        an_asset, resources={"inprocess_client": InProcessPipesClient()}
    )
    assert result.success
    assert called["yes"]