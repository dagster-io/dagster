from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import instance_for_test, poll_for_event, poll_for_finished_run
from dagster.grpc.server import ExecuteExternalPipelineArgs

from .utils import get_foo_grpc_pipeline_handle


def _get_engine_events(event_records):
    for er in event_records:
        if er.dagster_event and er.dagster_event.is_engine_event:
            yield er


def test_launch_run_grpc():
    with instance_for_test() as instance:
        with get_foo_grpc_pipeline_handle() as pipeline_handle:
            api_client = pipeline_handle.repository_handle.repository_location_handle.client

            pipeline_run = instance.create_run(
                pipeline_name="foo",
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
            run_id = pipeline_run.run_id

            res = api_client.start_run(
                ExecuteExternalPipelineArgs(
                    pipeline_origin=pipeline_handle.get_external_origin(),
                    pipeline_run_id=run_id,
                    instance_ref=instance.get_ref(),
                )
            )

            assert res.success
            finished_pipeline_run = poll_for_finished_run(instance, run_id)

            assert finished_pipeline_run
            assert finished_pipeline_run.run_id == run_id
            assert finished_pipeline_run.status == PipelineRunStatus.SUCCESS

            poll_for_event(
                instance, run_id, event_type="ENGINE_EVENT", message="Process for pipeline exited"
            )
            event_records = instance.all_logs(run_id)

            (started_process, executing_steps, finished_steps, process_exited) = tuple(
                _get_engine_events(event_records)
            )

            assert "Started process for pipeline" in started_process.message
            assert "Executing steps in process" in executing_steps.message
            assert "Finished steps in process" in finished_steps.message
            assert "Process for pipeline exited" in process_exited.message


def test_launch_unloadable_run_grpc():
    with instance_for_test() as instance:
        with get_foo_grpc_pipeline_handle() as pipeline_handle:
            api_client = pipeline_handle.repository_handle.repository_location_handle.client

            pipeline_run = instance.create_run(
                pipeline_name="foo",
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
            run_id = pipeline_run.run_id

            with instance_for_test() as other_instance:
                res = api_client.start_run(
                    ExecuteExternalPipelineArgs(
                        pipeline_origin=pipeline_handle.get_external_origin(),
                        pipeline_run_id=run_id,
                        instance_ref=other_instance.get_ref(),
                    )
                )

                assert not res.success
                assert (
                    "gRPC server could not load run {run_id} in order to execute it. "
                    "Make sure that the gRPC server has access to your run storage.".format(
                        run_id=run_id
                    )
                    in res.serializable_error_info.message
                )
