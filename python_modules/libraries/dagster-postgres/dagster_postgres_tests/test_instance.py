import os

import pytest
from dagster_postgres.event_log import PostgresEventLogStorage
from dagster_postgres.run_storage import PostgresRunStorage

from dagster import DagsterEventType, RunConfig, execute_pipeline, pipeline, seven, solid
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.root import LocalArtifactStorage


@pipeline
def simple():
    @solid
    def easy(context):
        context.log.info('easy')
        return 'easy'

    easy()


@pytest.mark.skipif(
    bool(os.getenv('BUILDKITE')), reason='Strange Docker networking issues on Buildkite'
)
def test_postgres_instance(multi_postgres):
    run_storage_conn_string, event_log_storage_conn_string = multi_postgres

    run_storage = PostgresRunStorage.create_clean_storage(run_storage_conn_string)
    event_storage = PostgresEventLogStorage.create_clean_storage(event_log_storage_conn_string)

    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance(
            instance_type=InstanceType.PERSISTENT,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=run_storage,
            event_storage=event_storage,
            compute_log_manager=LocalComputeLogManager(temp_dir),
        )

        run = RunConfig()
        execute_pipeline(simple, run_config=run, instance=instance)

        assert run_storage.has_run(run.run_id)
        assert run_storage.get_run_by_id(run.run_id).status == PipelineRunStatus.SUCCESS
        assert DagsterEventType.PIPELINE_SUCCESS in [
            event.dagster_event.event_type
            for event in event_storage.get_logs_for_run(run.run_id)
            if event.is_dagster_event
        ]
        stats = event_storage.get_stats_for_run(run.run_id)
        assert stats.steps_succeeded == 1
        assert stats.end_time is not None
