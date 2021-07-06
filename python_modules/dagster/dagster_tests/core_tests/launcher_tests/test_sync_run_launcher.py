from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import instance_for_test, poll_for_finished_run

from .test_default_run_launcher import get_deployed_grpc_server_workspace, noop_pipeline


def test_launch_run_backcompat():
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster.core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            }
        },
    ) as instance:
        with get_deployed_grpc_server_workspace(instance) as workspace:

            external_pipeline = (
                workspace.get_repository_location("test")
                .get_repository("nope")
                .get_full_external_pipeline("noop_pipeline")
            )

            pipeline_run = instance.create_run_for_pipeline(
                pipeline_def=noop_pipeline,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=None,  # no python origin set
            )
            run_id = pipeline_run.run_id

            assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

            instance.launch_run(run_id=pipeline_run.run_id, workspace=workspace)

            pipeline_run = instance.get_run_by_id(run_id)
            assert pipeline_run
            assert pipeline_run.run_id == run_id

            pipeline_run = poll_for_finished_run(instance, run_id)
            assert pipeline_run.status == PipelineRunStatus.SUCCESS
