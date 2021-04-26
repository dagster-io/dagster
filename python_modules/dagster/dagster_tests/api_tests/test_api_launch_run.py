from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import instance_for_test, poll_for_event, poll_for_finished_run
from dagster.grpc.server import ExecuteExternalPipelineArgs

from .utils import get_foo_pipeline_handle


def _check_event_log_contains(event_log, expected_type_and_message):
    types_and_messages = [
        (e.dagster_event.event_type_value, e.message) for e in event_log if e.is_dagster_event
    ]
    for expected_event_type, expected_message_fragment in expected_type_and_message:
        assert any(
            event_type == expected_event_type and expected_message_fragment in message
            for event_type, message in types_and_messages
        )


def test_launch_run_with_unloadable_pipeline_grpc():
    with instance_for_test() as instance:
        with get_foo_pipeline_handle() as pipeline_handle:
            api_client = pipeline_handle.repository_handle.repository_location.client

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

            original_origin = pipeline_handle.get_external_origin()

            # point the api to a pipeline that cannot be loaded
            res = api_client.start_run(
                ExecuteExternalPipelineArgs(
                    pipeline_origin=original_origin._replace(pipeline_name="i_am_fake_pipeline"),
                    pipeline_run_id=run_id,
                    instance_ref=instance.get_ref(),
                )
            )

            assert res.success
            finished_pipeline_run = poll_for_finished_run(instance, run_id)

            assert finished_pipeline_run
            assert finished_pipeline_run.run_id == run_id
            assert finished_pipeline_run.status == PipelineRunStatus.FAILURE

            poll_for_event(
                instance, run_id, event_type="ENGINE_EVENT", message="Process for pipeline exited"
            )
            event_records = instance.all_logs(run_id)
            _check_event_log_contains(
                event_records,
                [
                    ("ENGINE_EVENT", "Started process for pipeline"),
                    ("ENGINE_EVENT", "Could not load pipeline definition"),
                    (
                        "PIPELINE_FAILURE",
                        "This pipeline run has been marked as failed from outside the execution context",
                    ),
                    ("ENGINE_EVENT", "Process for pipeline exited"),
                ],
            )


def test_launch_run_grpc():
    with instance_for_test() as instance:
        with get_foo_pipeline_handle() as pipeline_handle:
            api_client = pipeline_handle.repository_handle.repository_location.client

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
            _check_event_log_contains(
                event_records,
                [
                    ("ENGINE_EVENT", msg)
                    for msg in [
                        "Started process for pipeline",
                        "Executing steps in process",
                        "Finished steps in process",
                        "Process for pipeline exited",
                    ]
                ],
            )


def test_launch_unloadable_run_grpc():
    with instance_for_test() as instance:
        with get_foo_pipeline_handle() as pipeline_handle:
            api_client = pipeline_handle.repository_handle.repository_location.client

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
