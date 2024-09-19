import time

from dagster._core.remote_representation.handle import JobHandle
from dagster._core.test_utils import create_run_for_test, instance_for_test, poll_for_event
from dagster._grpc.server import ExecuteExternalJobArgs
from dagster._grpc.types import CancelExecutionRequest, CancelExecutionResult, StartRunResult
from dagster._serdes.serdes import deserialize_value

from dagster_tests.api_tests.utils import get_bar_repo_code_location


def test_launch_run_grpc():
    with instance_for_test() as instance:
        with get_bar_repo_code_location(instance) as code_location:
            job_handle = JobHandle("forever", code_location.get_repository("bar_repo").handle)
            api_client = code_location.client

            run = create_run_for_test(instance, job_name="forever")
            run_id = run.run_id

            assert code_location.get_current_runs() == []

            res = deserialize_value(
                api_client.start_run(
                    ExecuteExternalJobArgs(
                        job_origin=job_handle.get_external_origin(),
                        run_id=run_id,
                        instance_ref=instance.get_ref(),
                    )
                ),
                StartRunResult,
            )
            assert res.success

            assert code_location.get_current_runs() == [run_id]

            res = deserialize_value(
                api_client.cancel_execution(CancelExecutionRequest(run_id=run_id)),
                CancelExecutionResult,
            )
            assert res.success

            poll_for_event(
                instance, run_id, event_type="ENGINE_EVENT", message="Process for run exited"
            )

            # have to wait for grpc server cleanup thread to run
            time.sleep(1)
            assert code_location.get_current_runs() == []
