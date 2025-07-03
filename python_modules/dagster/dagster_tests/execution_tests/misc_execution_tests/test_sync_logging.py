from collections.abc import Iterator

import dagster as dg
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.execution.context.compute import AssetExecutionContext, OpExecutionContext
from dagster._core.instance import DagsterInstance


def assert_latest_mat_metadata_entry(
    instance: DagsterInstance, asset_key: CoercibleToAssetKey, key: str, value: str
):
    mat_event = instance.get_latest_materialization_event(AssetKey.from_coercible(asset_key))
    assert mat_event
    assert mat_event.asset_materialization
    assert mat_event.asset_materialization.metadata[key] == dg.TextMetadataValue(value)


def test_op_that_yields() -> None:
    ran = {}

    @dg.op
    def op_that_yields(context: OpExecutionContext) -> Iterator:
        asset_key = dg.AssetKey("some_asset_key")
        yield dg.AssetMaterialization(asset_key=asset_key, metadata={"when": "during_run"})
        assert_latest_mat_metadata_entry(context.instance, asset_key, "when", "during_run")
        ran["yup"] = True
        yield dg.Output(value=None, metadata={"when": "after_run"})

    @dg.job
    def job_that_yields() -> None:
        op_that_yields()

    instance = DagsterInstance.ephemeral()
    assert job_that_yields.execute_in_process(instance=instance).success
    assert ran["yup"]


def test_op_that_logs_event() -> None:
    ran = {}

    @dg.op
    def op_that_yields(context: OpExecutionContext) -> Iterator:
        asset_key = dg.AssetKey("some_asset_key")
        context.log_event(
            dg.AssetMaterialization(asset_key=asset_key, metadata={"when": "during_run"})
        )
        assert_latest_mat_metadata_entry(context.instance, asset_key, "when", "during_run")
        ran["yup"] = True
        yield dg.Output(value=None, metadata={"when": "after_run"})

    @dg.job
    def job_that_yields() -> None:
        op_that_yields()

    instance = DagsterInstance.ephemeral()
    assert job_that_yields.execute_in_process(instance=instance).success
    assert ran["yup"]


def test_op_that_logs_event_with_implicit_yield() -> None:
    ran = {}

    @dg.op
    def op_that_yields(context: OpExecutionContext) -> None:
        asset_key = dg.AssetKey("some_asset_key")
        context.log_event(
            dg.AssetMaterialization(asset_key=asset_key, metadata={"when": "during_run"})
        )
        assert_latest_mat_metadata_entry(context.instance, asset_key, "when", "during_run")
        ran["yup"] = True

    @dg.job
    def job_that_yields() -> None:
        op_that_yields()

    instance = DagsterInstance.ephemeral()
    assert job_that_yields.execute_in_process(instance=instance).success
    assert ran["yup"]


def test_asset_that_logs_on_other_asset() -> None:
    ran = {}

    logs_other_asset_key = dg.AssetKey("logs_other_asset")

    @dg.asset(key=logs_other_asset_key)
    def asset_that_logs_mat_on_other_asset(context: AssetExecutionContext) -> None:
        context.log_event(
            dg.AssetMaterialization(asset_key="other_asset", metadata={"when": "during_run"})
        )
        assert_latest_mat_metadata_entry(context.instance, "other_asset", "when", "during_run")
        context.add_output_metadata({"when": "after_run"})
        # test that it is not yet present
        assert context.instance.get_latest_materialization_event(logs_other_asset_key) is None
        ran["yup"] = True

    instance = DagsterInstance.ephemeral()
    assert dg.materialize([asset_that_logs_mat_on_other_asset], instance=instance).success
    assert ran["yup"]
    assert_latest_mat_metadata_entry(instance, logs_other_asset_key, "when", "after_run")


def test_asset_that_logs_on_itself() -> None:
    ran = {}

    logs_itself_key = dg.AssetKey("logs_itself")

    @dg.asset(key=logs_itself_key)
    def asset_that_logs_mat_on_other_asset(context: AssetExecutionContext) -> None:
        context.log_event(
            dg.AssetMaterialization(asset_key=logs_itself_key, metadata={"when": "during_run"})
        )
        assert_latest_mat_metadata_entry(context.instance, logs_itself_key, "when", "during_run")
        context.add_output_metadata({"when": "after_run"})
        # assert not overwritten
        assert_latest_mat_metadata_entry(context.instance, logs_itself_key, "when", "during_run")
        ran["yup"] = True

    instance = DagsterInstance.ephemeral()
    assert dg.materialize([asset_that_logs_mat_on_other_asset], instance=instance).success
    assert ran["yup"]
    assert_latest_mat_metadata_entry(instance, logs_itself_key, "when", "after_run")
