from abc import ABCMeta, abstractmethod
from collections import namedtuple, defaultdict

import six

from dagster import check

from .execution import execute_marshalling
from .execution_context import RunConfiguration
from .execution_plan.objects import ExecutionStepEvent, ExecutionStepEventType
from .execution_plan.plan_subset import StepExecution


class SerializableExecutionMetadata(namedtuple('_SerializableExecutionMetadata', 'run_id tags')):
    def __new__(cls, run_id, tags):
        return super(SerializableExecutionMetadata, cls).__new__(
            cls,
            check.str_param(run_id, 'run_id'),
            check.dict_param(tags, 'tags', key_type=str, value_type=str),
        )


class SerializableStepOutputEvent(
    namedtuple('_SerializableStepOutputEvent', 'event_type step_key output_name value_repr')
):
    def __new__(cls, event_type, step_key, output_name, value_repr):
        return super(SerializableStepOutputEvent, cls).__new__(
            cls,
            check.inst_param(event_type, 'event_type', ExecutionStepEventType),
            check.str_param(step_key, 'step_key'),
            check.str_param(output_name, 'output_name'),
            check.str_param(value_repr, 'value_repr'),
        )


class SerializableStepFailureEvent(
    namedtuple('_SerializableStepFailureEvent', 'event_type step_key error_message')
):
    def __new__(cls, event_type, step_key, error_message):
        return super(SerializableStepFailureEvent, cls).__new__(
            cls,
            check.inst_param(event_type, 'event_type', ExecutionStepEventType),
            check.str_param(step_key, 'step_key'),
            check.str_param(error_message, 'error_message'),
        )


SerializableStepEvents = (SerializableStepOutputEvent, SerializableStepFailureEvent)


def list_pull(alist, key):
    return list(map(lambda elem: getattr(elem, key), alist))


def input_marshalling_dict_from_step_executions(step_executions):
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
            event_type=step_event.event_type,
            step_key=step_event.step.key,
            output_name=step_event.step_output_data.output_name,
            value_repr=step_event.step_output_data.value_repr,
        )
    elif step_event.is_step_failure:
        return SerializableStepFailureEvent(
            event_type=step_event.event_type,
            step_key=step_event.step.key,
            error_message=str(step_event.step_failure_data.dagster_error),
        )

    check.failed('Unsupported step_event type {}'.format(step_event))


class PipelineFactory(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    '''
    Made this a factory protocol so that we can reconstruct pipelines in other
    processes through different means. We may want to reconstruct a pipeline
    from the information that is the passed to dagit rather than relying
    on pickling to remote a function over to another process. 
    '''

    @abstractmethod
    def construct_pipeline(self):
        pass


class ForkedProcessPipelineFactory(
    PipelineFactory, namedtuple('_ForkedProcessPipelineFactory', 'pipeline_fn')
):
    def construct_pipeline(self):
        return self.pipeline_fn()


def execute_serializable_execution_plan(
    pipeline_factory, environment_dict, run_configuration, step_executions
):
    check.inst_param(pipeline_factory, 'pipeline_factory', PipelineFactory)
    check.dict_param(environment_dict, 'enviroment_dict', key_type=str)
    check.inst_param(run_configuration, 'run_configuration', SerializableExecutionMetadata)
    check.list_param(step_executions, 'step_executions', of_type=StepExecution)

    step_events = execute_marshalling(
        pipeline_factory.construct_pipeline(),
        environment_dict=environment_dict,
        step_keys=list_pull(step_executions, 'step_key'),
        inputs_to_marshal=input_marshalling_dict_from_step_executions(step_executions),
        outputs_to_marshal={se.step_key: se.marshalled_outputs for se in step_executions},
        run_configuration=RunConfiguration(
            run_id=run_configuration.run_id, tags=run_configuration.tags
        ),
        throw_on_user_error=False,
    )

    return list(map(_to_serializable_step_event, step_events))
