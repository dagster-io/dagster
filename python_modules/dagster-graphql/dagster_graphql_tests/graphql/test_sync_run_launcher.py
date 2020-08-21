from dagster import DagsterInstance, seven
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.test_utils import create_run_for_test

from .setup import get_main_external_repo


def test_sync_run_launcher_from_configurable_class():
    with seven.TemporaryDirectory() as temp_dir:
        instance_no_hijack = DagsterInstance.local_temp(
            temp_dir,
            overrides={
                "run_launcher": {
                    "module": "dagster.core.launcher.sync_in_memory_run_launcher",
                    "class": "SyncInMemoryRunLauncher",
                }
            },
        )

        assert isinstance(instance_no_hijack.run_launcher, SyncInMemoryRunLauncher)


def test_sync_run_launcher_run():
    external_repo = get_main_external_repo()
    external_pipeline = external_repo.get_full_external_pipeline("noop_pipeline")

    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(
            temp_dir,
            overrides={
                "run_launcher": {
                    "module": "dagster.core.launcher.sync_in_memory_run_launcher",
                    "class": "SyncInMemoryRunLauncher",
                }
            },
        )

        run = create_run_for_test(instance=instance, pipeline_name=external_pipeline.name)

        run = instance.run_launcher.launch_run(
            instance=instance, run=run, external_pipeline=external_pipeline
        )

        completed_run = instance.get_run_by_id(run.run_id)
        assert completed_run.is_success
