from dagster import mem_io_manager
from dagster_test.toys.asset_reconciliation.eager_reconciliation import defs


def test_assets():
    defs.resolve_implicit_global_asset_job_def().execute_in_process(
        resources={"io_manager": mem_io_manager}
    )
