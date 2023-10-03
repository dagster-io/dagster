from dagster import (
    Definitions,
    MaterializeResult,
    TextMetadataValue,
    asset,
)
from dagster_pipes import (
    PipesContext,
)

from .in_process_client import (
    InProcessPipesClient,
    InProcessPipesMessageWriteChannel,
    InProcessPipesMessageWriter,
)


def test_inprocess_writer_init() -> None:
    assert InProcessPipesMessageWriteChannel()
    writer = InProcessPipesMessageWriter()
    assert isinstance(writer.write_channel, InProcessPipesMessageWriteChannel)


def test_basic_in_process() -> None:
    called = {}

    def _impl(context: PipesContext):
        context.report_asset_materialization(metadata={"test_key": "test_value"})
        called["impl"] = True

    @asset
    def an_asset(context, inprocess_client: InProcessPipesClient) -> MaterializeResult:
        completed_invocation = inprocess_client.run(context=context, fn=_impl)
        materialize_result = completed_invocation.get_materialize_result()
        called["orch"] = True
        assert materialize_result.asset_key
        assert materialize_result.asset_key.to_user_string() == "an_asset"
        assert materialize_result.metadata
        assert isinstance(materialize_result.metadata["test_key"], TextMetadataValue)
        assert materialize_result.metadata["test_key"].value == "test_value"
        return materialize_result

    defs = Definitions(assets=[an_asset], resources={"inprocess_client": InProcessPipesClient()})
    exec_result = defs.get_implicit_global_asset_job_def().execute_in_process()
    assert exec_result.success
    assert called["impl"]
    assert called["orch"]
