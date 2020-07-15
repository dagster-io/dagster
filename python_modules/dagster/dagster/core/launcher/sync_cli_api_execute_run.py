'''This file is used by the EphemeralGrpcRunLauncher to execute runs in a subprocess.'''
import sys

from dagster import check
from dagster.api.execute_run import cli_api_execute_run_grpc
from dagster.core.instance import DagsterInstance, InstanceRef
from dagster.core.origin import PipelinePythonOrigin
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.serdes.ipc import setup_interrupt_support
from dagster.seven import json

if __name__ == '__main__':
    setup_interrupt_support()
    kwargs = json.loads(sys.argv[1])
    instance_ref = check.inst(
        deserialize_json_to_dagster_namedtuple(kwargs['instance_ref']), InstanceRef
    )
    pipeline_origin = check.inst(
        deserialize_json_to_dagster_namedtuple(kwargs['pipeline_origin']), PipelinePythonOrigin
    )
    pipeline_run_id = kwargs['pipeline_run_id']
    instance = DagsterInstance.from_ref(instance_ref)
    pipeline_run = instance.get_run_by_id(pipeline_run_id)
    events = [
        evt
        for evt in cli_api_execute_run_grpc(
            instance_ref=instance_ref, pipeline_origin=pipeline_origin, pipeline_run=pipeline_run
        )
    ]
    print(len(events))
