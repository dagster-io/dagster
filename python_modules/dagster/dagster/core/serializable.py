from collections import namedtuple, defaultdict
from dagster import check

from .errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvalidSubplanInputNotFoundError,
    DagsterInvalidSubplanMissingInputError,
    DagsterInvalidSubplanOutputNotFoundError,
    DagsterUserCodeExecutionError,
)
from .execution import execute_marshalling, create_execution_plan
from .execution_context import ExecutionMetadata
from .execution_plan.objects import ExecutionStepEvent
from .execution_plan.plan_subset import MarshalledOutput, MarshalledInput, StepExecution


SerializableExecutionMetadata = namedtuple('SerializableExecutionMetadata', 'run_id tags')
SerializableExecutionTag = namedtuple('SerialiableExecutionTag', 'key value')

SerializableStepOutputEvent = namedtuple(
    'SerializableStepOutputEvent', 'success step_key output_name value_repr'
)

SerializableStepFailureEvent = namedtuple(
    'SerializableStepFailureEvent', 'success step_key error_message'
)


def list_pull(alist, key):
    return list(map(lambda elem: getattr(elem, key), alist))


def _get_inputs_to_marshal(step_executions):
    check.list_param(step_executions, 'step_executions', of_type=StepExecution)
    inputs_to_marshal = defaultdict(dict)
    for step_execution in step_executions:
        for input_name, marshalling_key in step_execution.marshalled_inputs:
            inputs_to_marshal[step_execution.step_key][input_name] = marshalling_key
    return dict(inputs_to_marshal)


def _to_serializable_step_event(step_event):
    check.inst_param(step_event, 'step_event', ExecutionStepEvent)

    if step_event.is_successful_output:
        return SerializableStepOutputEvent(
            success=step_event.is_successful_output,
            step_key=step_event.step.key,
            output_name=step_event.success_data.output_name,
            value_repr=repr(step_event.success_data.value),
        )
    elif step_event.is_step_failure:
        return SerializableStepFailureEvent(
            success=step_event.is_successful_output,
            step_key=step_event.step.key,
            error_message=str(step_event.failure_data.dagster_error),
        )

    check.failed('Unsupported step_event type {}'.format(step_event))


def serializable_execution_plan(pipeline_fn, environment_dict, execution_metadata, step_executions):
    check.callable_param(pipeline_fn, 'pipeline_fn')
    check.dict_param(environment_dict, 'enviroment_dict', key_type=str)
    check.inst_param(execution_metadata, 'execution_metadata', SerializableExecutionMetadata)
    check.list_param(step_executions, 'step_executions', of_type=StepExecution)

    # try:
    step_events = execute_marshalling(
        pipeline_fn(),
        step_keys=list_pull(step_executions, 'step_key'),
        inputs_to_marshal=_get_inputs_to_marshal(step_executions),
        outputs_to_marshal={se.step_key: se.marshalled_outputs for se in step_executions},
        execution_metadata=ExecutionMetadata(
            run_id=execution_metadata.run_id, tags={t.key: t.value for t in execution_metadata.tags}
        ),
        throw_on_user_error=False,
    )
    # except DagsterInvalidSubplanMissingInputError as invalid_subplan_error:
    #     pass

    # except DagsterInvalidSubplanOutputNotFoundError as output_not_found_error:
    #     pass

    # except DagsterInvalidSubplanInputNotFoundError as input_not_found_error:
    #     pass

    # except DagsterExecutionStepNotFoundError as step_not_found_error:
    #     pass

    return list(map(_to_serializable_step_event, step_events))

