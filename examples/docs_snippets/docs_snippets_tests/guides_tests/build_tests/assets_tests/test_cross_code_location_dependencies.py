from dagster._core.test_utils import instance_for_test
from docs_snippets.guides.build.assets.cross_code_location_dependencies import defs


def test_cross_code_location_io_manager_loading():
    with instance_for_test() as instance:
        assert (
            defs.get_implicit_global_asset_job_def()
            .execute_in_process(instance=instance)
            .success
        )
