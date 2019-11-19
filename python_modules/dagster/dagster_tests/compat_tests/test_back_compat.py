from dagster import file_relative_path
from dagster.core.instance import DagsterInstance, InstanceRef


# test that we can load runs and events from an old instance
def test_0_6_4():
    instance = DagsterInstance.from_ref(
        InstanceRef.from_dir(file_relative_path(__file__, 'snapshot_0_6_4'))
    )

    runs = instance.all_runs()
    for run in runs:
        instance.all_logs(run.run_id)
