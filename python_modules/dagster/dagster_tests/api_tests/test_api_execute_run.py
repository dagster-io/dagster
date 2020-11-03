from dagster.api.execute_run import sync_execute_run_grpc
from dagster.core.test_utils import instance_for_test
from dagster.grpc.server import GrpcServerProcess

from .utils import get_foo_grpc_pipeline_handle, get_foo_pipeline_handle


def test_execute_run_api_grpc_server_handle():
    with instance_for_test() as instance:
        with get_foo_grpc_pipeline_handle() as pipeline_handle:
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
            events = [
                event
                for event in sync_execute_run_grpc(
                    api_client=pipeline_handle.repository_handle.repository_location_handle.client,
                    instance_ref=instance.get_ref(),
                    pipeline_origin=pipeline_handle.get_external_origin(),
                    pipeline_run=pipeline_run,
                )
            ]

    assert len(events) == 17
    assert [event.event_type_value for event in events] == [
        "ENGINE_EVENT",
        "ENGINE_EVENT",
        "PIPELINE_START",
        "ENGINE_EVENT",
        "STEP_START",
        "STEP_OUTPUT",
        "OBJECT_STORE_OPERATION",
        "STEP_SUCCESS",
        "STEP_START",
        "OBJECT_STORE_OPERATION",
        "STEP_INPUT",
        "STEP_OUTPUT",
        "OBJECT_STORE_OPERATION",
        "STEP_SUCCESS",
        "ENGINE_EVENT",
        "PIPELINE_SUCCESS",
        "ENGINE_EVENT",
    ]


def test_execute_run_api_grpc_python_handle():
    with instance_for_test() as instance:
        with get_foo_pipeline_handle() as pipeline_handle:
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

            loadable_target_origin = (
                pipeline_handle.get_external_origin().external_repository_origin.repository_location_origin.loadable_target_origin
            )

            server_process = GrpcServerProcess(loadable_target_origin, max_workers=2)
            with server_process.create_ephemeral_client() as api_client:
                events = [
                    event
                    for event in sync_execute_run_grpc(
                        api_client=api_client,
                        instance_ref=instance.get_ref(),
                        pipeline_origin=pipeline_handle.get_external_origin(),
                        pipeline_run=pipeline_run,
                    )
                ]

                assert len(events) == 17
                assert [event.event_type_value for event in events] == [
                    "ENGINE_EVENT",
                    "ENGINE_EVENT",
                    "PIPELINE_START",
                    "ENGINE_EVENT",
                    "STEP_START",
                    "STEP_OUTPUT",
                    "OBJECT_STORE_OPERATION",
                    "STEP_SUCCESS",
                    "STEP_START",
                    "OBJECT_STORE_OPERATION",
                    "STEP_INPUT",
                    "STEP_OUTPUT",
                    "OBJECT_STORE_OPERATION",
                    "STEP_SUCCESS",
                    "ENGINE_EVENT",
                    "PIPELINE_SUCCESS",
                    "ENGINE_EVENT",
                ]
            server_process.wait()
