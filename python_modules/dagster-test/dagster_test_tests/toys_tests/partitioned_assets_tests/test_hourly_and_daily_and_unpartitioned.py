from dagster import Definitions, load_assets_from_modules
from dagster_test.toys.partitioned_assets import hourly_and_daily_and_unpartitioned


def test_assets():
    defs = Definitions(assets=load_assets_from_modules([hourly_and_daily_and_unpartitioned]))
    for job_name in defs.get_repository_def().get_implicit_asset_job_names():
        job_def = defs.get_job_def(job_name)
        partition_key = job_def.partitioned_config.partitions_def.get_partition_keys()[0]
        assert job_def.execute_in_process(partition_key=partition_key).success
