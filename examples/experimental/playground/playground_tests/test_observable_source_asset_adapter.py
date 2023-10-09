import playground.observable_source_asset_adapter
from dagster import DagsterInstance


def test_observable_source_adapter() -> None:
    job_def = playground.observable_source_asset_adapter.defs.get_implicit_global_asset_job_def()
    instance = DagsterInstance.ephemeral()
    assert job_def.execute_in_process(instance=instance).success
