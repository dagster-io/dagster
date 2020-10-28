from dagster import check
from dagster.core.events import EngineEventData
from dagster.core.host_representation import ExternalPipelineOrigin
from dagster.core.instance import DagsterInstance
from dagster.core.instance.ref import InstanceRef
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.grpc.server import ExecuteExternalPipelineArgs
from dagster.serdes.ipc import IPCErrorMessage


def execute_run_grpc(api_client, instance_ref, pipeline_origin, pipeline_run):
    """Asynchronously execute a run over GRPC."""
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(instance_ref, "instance_ref", InstanceRef)
    check.inst_param(pipeline_origin, "pipeline_origin", ExternalPipelineOrigin)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)

    with DagsterInstance.from_ref(instance_ref) as instance:
        yield instance.report_engine_event(
            'About to start process for pipeline "{pipeline_name}" (run_id: {run_id}).'.format(
                pipeline_name=pipeline_run.pipeline_name, run_id=pipeline_run.run_id
            ),
            pipeline_run,
            engine_event_data=EngineEventData(marker_start="cli_api_subprocess_init"),
        )

        run_did_fail = False

        execute_run_args = ExecuteExternalPipelineArgs(
            pipeline_origin=pipeline_origin,
            pipeline_run_id=pipeline_run.run_id,
            instance_ref=instance_ref,
        )
        for event in api_client.execute_run(execute_run_args=execute_run_args):
            if isinstance(event, IPCErrorMessage):
                yield instance.report_engine_event(
                    event.message,
                    pipeline_run=pipeline_run,
                    engine_event_data=EngineEventData(
                        marker_end="cli_api_subprocess_init", error=event.serializable_error_info
                    ),
                )
                if not run_did_fail:
                    run_did_fail = True
                    yield instance.report_run_failed(pipeline_run)
            else:
                yield event


def sync_execute_run_grpc(api_client, instance_ref, pipeline_origin, pipeline_run):
    """Synchronous version of execute_run_grpc."""
    return [
        event
        for event in execute_run_grpc(
            api_client=api_client,
            instance_ref=instance_ref,
            pipeline_origin=pipeline_origin,
            pipeline_run=pipeline_run,
        )
    ]
