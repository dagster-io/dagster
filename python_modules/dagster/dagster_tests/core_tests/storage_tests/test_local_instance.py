from dagster import DagsterEventType, RunConfig, execute_pipeline, lambda_solid, pipeline, seven
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.storage.event_log import FilesystemEventLogStorage
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.runs import FilesystemRunStorage


def test_fs_stores():
    @pipeline
    def simple():
        @lambda_solid
        def easy():
            return 'easy'

        easy()

    with seven.TemporaryDirectory() as temp_dir:
        run_store = FilesystemRunStorage(temp_dir)
        event_store = FilesystemEventLogStorage(temp_dir)
        instance = DagsterInstance(
            instance_type=InstanceType.LOCAL,
            root_storage_dir=temp_dir,
            run_storage=run_store,
            event_storage=event_store,
        )

        run = RunConfig()
        execute_pipeline(simple, run_config=run, instance=instance)

        assert run_store.has_run(run.run_id)
        assert run_store.get_run_by_id(run.run_id).status == PipelineRunStatus.SUCCESS
        assert DagsterEventType.PIPELINE_SUCCESS in [
            event.dagster_event.event_type for event in event_store.get_logs_for_run(run.run_id)
        ]
