import time

from dagster._core.host_representation.handle import JobHandle
from dagster._core.test_utils import instance_for_test, poll_for_event
from dagster._grpc.server import ExecuteExternalPipelineArgs
from dagster._grpc.types import CancelExecutionRequest
from dagster._serdes import deserialize_json_to_dagster_namedtuple

from .utils import get_bar_repo_repository_location


def test_launch_run_grpc():
    with instance_for_test() as instance:
        with get_bar_repo_repository_location(instance) as repository_location:

            job_handle = JobHandle("forever", repository_location.get_repository("bar_repo").handle)
            api_client = repository_location.client

            run = instance.create_run(
                pipeline_name="forever",
                run_id=None,
                run_config={},
                mode="default",
                solids_to_execute=None,
                step_keys_to_execute=None,
                status=None,
                tags=None,
                root_run_id=None,
                parent_run_id=None,
                pipeline_snapshot=None,
                execution_plan_snapshot=None,
                parent_pipeline_snapshot=None,
            )
            run_id = run.run_id

            assert repository_location.get_current_runs() == []

            res = deserialize_json_to_dagster_namedtuple(
                api_client.start_run(
                    ExecuteExternalPipelineArgs(
                        pipeline_origin=job_handle.get_external_origin(),
                        pipeline_run_id=run_id,
                        instance_ref=instance.get_ref(),
                    )
                )
            )
            assert res.success

            assert repository_location.get_current_runs() == [run_id]

            res = deserialize_json_to_dagster_namedtuple(
                api_client.cancel_execution(CancelExecutionRequest(run_id=run_id))
            )
            assert res.success

            poll_for_event(
                instance, run_id, event_type="ENGINE_EVENT", message="Process for run exited"
            )

            # have to wait for grpc server cleanup thread to run
            time.sleep(1)
            assert repository_location.get_current_runs() == []
