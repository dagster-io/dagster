from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.test_utils import create_run_for_test, instance_for_test

from .setup import get_main_external_repo


def test_sync_run_launcher_from_configurable_class():
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster.core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            }
        },
    ) as instance_no_hijack:
        assert isinstance(instance_no_hijack.run_launcher, SyncInMemoryRunLauncher)


def test_sync_run_launcher_run():
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster.core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            }
        },
    ) as instance:
        with get_main_external_repo() as external_repo:
            external_pipeline = external_repo.get_full_external_pipeline("noop_pipeline")

            run = create_run_for_test(instance=instance, pipeline_name=external_pipeline.name)

            run = instance.launch_run(run_id=run.run_id, external_pipeline=external_pipeline)

            completed_run = instance.get_run_by_id(run.run_id)
            assert completed_run.is_success
