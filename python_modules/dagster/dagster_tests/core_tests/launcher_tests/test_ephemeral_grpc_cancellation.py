import sys
import threading
import time

from dagster import Field, Int, Materialization, pipeline, repository, solid
from dagster.core.origin import PipelineGrpcServerOrigin, RepositoryGrpcServerOrigin
from dagster.core.test_utils import instance_for_test, poll_for_finished_run, poll_for_step_start
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.server import GrpcServerProcess
from dagster.grpc.types import CancelExecutionRequest, ExecuteRunArgs


@solid(config_schema={"length": Field(Int)}, output_defs=[])
def streamer(context):
    for i in range(context.solid_config["length"]):
        yield Materialization(label=str(i))
        time.sleep(0.1)


@pipeline
def streaming_pipeline():
    streamer()


@repository
def test_repository():
    return [streaming_pipeline]


def _stream_events_target(results, api_client, execute_run_args):
    for result in api_client.execute_run(execute_run_args):
        results.append(result)


def test_cancel_run():
    with instance_for_test() as instance:

        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable, python_file=__file__, working_directory=None,
        )

        server_process = GrpcServerProcess(loadable_target_origin, max_workers=10)

        with server_process.create_ephemeral_client() as api_client:
            streaming_results = []

            pipeline_run = instance.create_run_for_pipeline(
                streaming_pipeline, run_config={"solids": {"streamer": {"config": {"length": 20}}}},
            )
            execute_run_args = ExecuteRunArgs(
                pipeline_origin=PipelineGrpcServerOrigin(
                    pipeline_name="streaming_pipeline",
                    repository_origin=RepositoryGrpcServerOrigin(
                        host="localhost",
                        socket=api_client.socket,
                        port=api_client.port,
                        repository_name="test_repository",
                    ),
                ),
                pipeline_run_id=pipeline_run.run_id,
                instance_ref=instance.get_ref(),
            )
            stream_events_result_thread = threading.Thread(
                target=_stream_events_target, args=[streaming_results, api_client, execute_run_args]
            )
            stream_events_result_thread.daemon = True
            stream_events_result_thread.start()
            poll_for_step_start(instance, pipeline_run.run_id)

            res = api_client.cancel_execution(
                cancel_execution_request=CancelExecutionRequest(run_id=pipeline_run.run_id)
            )
            assert res.success is True

            poll_for_finished_run(instance, pipeline_run.run_id)

            logs = instance.all_logs(pipeline_run.run_id)
            assert (
                len(
                    [
                        ev
                        for ev in logs
                        if ev.dagster_event.event_type_value == "STEP_MATERIALIZATION"
                    ]
                )
                < 20
            )

            # soft termination
            assert [ev for ev in logs if ev.dagster_event.event_type_value == "STEP_FAILURE"]

        server_process.wait()
