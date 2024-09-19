import docs_snippets.concepts.assets.external_assets.update_external_asset_via_op
from dagster import AssetKey, DagsterInstance, Definitions


def test_external_assets_update_external_asset_via_op_0() -> None:
    defs: Definitions = (
        docs_snippets.concepts.assets.external_assets.update_external_asset_via_op.defs
    )
    a_job_def = defs.get_job_def("a_job")
    instance = DagsterInstance.ephemeral()
    result = a_job_def.execute_in_process(instance=instance)
    assert result.success

    assert instance.get_latest_materialization_event(AssetKey("external_asset"))
