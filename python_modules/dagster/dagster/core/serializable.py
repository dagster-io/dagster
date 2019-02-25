from collections import namedtuple
from dagster import check

from .execution import execute_marshalling
from .execution_plan.plan_subset import MarshalledOutput, MarshalledInput, StepExecution

SerializableExecutionMetadata = namedtuple('SerializableExecutionMetadata', 'run_id tags')
SerializableExecutionTag = namedtuple('SerialiableExecutionTag', 'key value')


def serializable_execution_plan(
    pipeline_name, environment_dict, execution_metadata, step_executions
):
    check.str_param(pipeline_name, 'pipeline_name')
    check.dict_param(environment_dict, 'enviroment_dict', key_type=str)
    check.inst_param(execution_metadata, 'execution_metadata', SerializableExecutionMetadata)
    check.list_param(step_executions, 'step_executions', of_type=StepExecution)

