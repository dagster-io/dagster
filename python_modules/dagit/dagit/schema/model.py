from __future__ import absolute_import
from collections import defaultdict, namedtuple
import sys
import uuid


from graphql.execution.base import ResolveInfo

from dagster import ExecutionMetadata, check
from dagster.core.execution_plan.objects import ExecutionStepEvent
from dagster.core.execution_plan.plan_subset import MarshalledOutput

from dagster.core.errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvalidSubplanInputNotFoundError,
    DagsterInvalidSubplanMissingInputError,
    DagsterInvalidSubplanOutputNotFoundError,
    DagsterUserCodeExecutionError,
)

from dagster.core.execution import (
    ExecutionSelector,
    create_execution_plan,
    execute_marshalling,
    get_subset_pipeline,
)
from dagster.core.types.evaluator import evaluate_config_value, EvaluateValueResult

from dagster.utils.error import serializable_error_info_from_exc_info

from .config_types import to_dauphin_config_type
from .errors import DauphinSuccessfulStepOutputEvent, DauphinStepFailureEvent
from .execution import DauphinExecutionStep
from .pipelines import DauphinPipeline
from .runtime_types import to_dauphin_runtime_type
from .utils import EitherValue, EitherError


def get_pipelines(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    return _get_pipelines(graphene_info).value()


def get_pipelines_or_raise(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    return _get_pipelines(graphene_info).value_or_raise()


def _get_pipelines(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)

    def process_pipelines(repository):
        pipeline_instances = []
        for pipeline_def in repository.get_all_pipelines():
            pipeline_instances.append(graphene_info.schema.type_named('Pipeline')(pipeline_def))
        return graphene_info.schema.type_named('PipelineConnection')(
            nodes=sorted(pipeline_instances, key=lambda pipeline: pipeline.name)
        )

    repository_or_error = _repository_or_error_from_container(
        graphene_info, graphene_info.context.repository_container
    )
    return repository_or_error.chain(process_pipelines)


def get_pipeline(graphene_info, selector):
    return _get_pipeline(graphene_info, selector).value()


def get_pipeline_or_raise(graphene_info, selector):
    return _get_pipeline(graphene_info, selector).value_or_raise()


def _get_pipeline(graphene_info, selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    return _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, selector
    )


def get_pipeline_type(graphene_info, pipelineName, typeName):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(pipelineName, 'pipelineName')
    check.str_param(typeName, 'typeName')
    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, ExecutionSelector(pipelineName)
    )
    return pipeline_or_error.chain(
        lambda pipeline: pipeline.get_type(graphene_info, typeName)
    ).value_or_raise()


def _config_type_or_error(graphene_info, dauphin_pipeline, config_type_name):
    pipeline = dauphin_pipeline.get_dagster_pipeline()
    if not pipeline.has_config_type(config_type_name):
        return EitherError(
            graphene_info.schema.type_named('ConfigTypeNotFoundError')(
                pipeline=pipeline, config_type_name=config_type_name
            )
        )
    else:
        dauphin_config_type = to_dauphin_config_type(pipeline.config_type_named(config_type_name))
        return EitherValue(dauphin_config_type)


def get_config_type(graphene_info, pipeline_name, type_name):
    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, ExecutionSelector(pipeline_name)
    )

    return pipeline_or_error.chain(
        lambda pipeline: _config_type_or_error(graphene_info, pipeline, type_name)
    ).value()


def _runtime_type_or_error(graphene_info, dauphin_pipeline, runtime_type_name):
    pipeline = dauphin_pipeline.get_dagster_pipeline()
    if not pipeline.has_runtime_type(runtime_type_name):
        return EitherError(
            graphene_info.schema.type_named('RuntimeTypeNotFoundError')(
                pipeline=pipeline, runtime_type_name=runtime_type_name
            )
        )
    else:
        dauphin_runtime_type = to_dauphin_runtime_type(
            pipeline.runtime_type_named(runtime_type_name)
        )
        return EitherValue(dauphin_runtime_type)


def get_runtime_type(graphene_info, pipeline_name, type_name):
    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, ExecutionSelector(pipeline_name)
    )

    return pipeline_or_error.chain(
        lambda pipeline: _runtime_type_or_error(graphene_info, pipeline, type_name)
    ).value()


def get_run(graphene_info, runId):
    pipeline_run_storage = graphene_info.context.pipeline_runs
    run = pipeline_run_storage.get_run_by_id(runId)
    if not run:
        raise Exception('No run with such id: {run_id}'.format(run_id=runId))
    else:
        return graphene_info.schema.type_named('PipelineRun')


def get_runs(graphene_info):
    pipeline_run_storage = graphene_info.context.pipeline_runs
    return [
        graphene_info.schema.type_named('PipelineRun')(run)
        for run in pipeline_run_storage.all_runs()
    ]


def validate_pipeline_config(graphene_info, selector, config):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    def do_validation(pipeline):
        config_or_error = _config_or_error_from_pipeline(graphene_info, pipeline, config)
        return config_or_error.chain(
            lambda config: graphene_info.schema.type_named('PipelineConfigValidationValid')(
                pipeline
            )
        )

    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, selector
    )
    return pipeline_or_error.chain(do_validation).value()


def get_execution_plan(graphene_info, selector, config):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    def create_plan(pipeline):
        config_or_error = _config_or_error_from_pipeline(graphene_info, pipeline, config)
        return config_or_error.chain(
            lambda evaluate_value_result: graphene_info.schema.type_named('ExecutionPlan')(
                pipeline,
                create_execution_plan(
                    pipeline.get_dagster_pipeline(),
                    evaluate_value_result.value,
                    ExecutionMetadata(),
                ),
            )
        )

    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, selector
    )
    return pipeline_or_error.chain(create_plan).value()


def start_pipeline_execution(graphene_info, selector, config):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    pipeline_run_storage = graphene_info.context.pipeline_runs
    env_config = config

    def get_config_and_start_execution(pipeline):
        def _start_execution(validated_config_either):
            new_run_id = str(uuid.uuid4())
            execution_plan = create_execution_plan(
                pipeline.get_dagster_pipeline(), validated_config_either.value, ExecutionMetadata()
            )
            run = pipeline_run_storage.create_run(new_run_id, selector, env_config, execution_plan)
            pipeline_run_storage.add_run(run)

            graphene_info.context.execution_manager.execute_pipeline(
                graphene_info.context.repository_container,
                pipeline.get_dagster_pipeline(),
                run,
                throw_on_user_error=graphene_info.context.throw_on_user_error,
            )
            return graphene_info.schema.type_named('StartPipelineExecutionSuccess')(
                run=graphene_info.schema.type_named('PipelineRun')(run)
            )

        config_or_error = _config_or_error_from_pipeline(graphene_info, pipeline, env_config)
        return config_or_error.chain(_start_execution)

    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, selector
    )
    return pipeline_or_error.chain(get_config_and_start_execution).value()


def get_pipeline_run_observable(graphene_info, run_id, after=None):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(run_id, 'run_id')
    check.opt_str_param(after, 'after')
    pipeline_run_storage = graphene_info.context.pipeline_runs
    run = pipeline_run_storage.get_run_by_id(run_id)
    if not run:
        raise Exception('No run with such id: {run_id}'.format(run_id=run_id))

    def get_observable(pipeline):
        pipeline_run_event_type = graphene_info.schema.type_named('PipelineRunEvent')
        return run.observable_after_cursor(after).map(
            lambda events: graphene_info.schema.type_named('PipelineRunLogsSubscriptionPayload')(
                messages=[
                    pipeline_run_event_type.from_dagster_event(graphene_info, event, pipeline)
                    for event in events
                ]
            )
        )

    return (
        _pipeline_or_error_from_container(
            graphene_info, graphene_info.context.repository_container, run.selector
        )
        .chain(get_observable)
        .value_or_raise()
    )


def _repository_or_error_from_container(graphene_info, container):
    error = container.error
    if error is not None:
        return EitherError(
            graphene_info.schema.type_named('PythonError')(
                serializable_error_info_from_exc_info(error)
            )
        )
    try:
        return EitherValue(container.repository)
    except Exception:  # pylint: disable=broad-except
        return EitherError(
            graphene_info.schema.type_named('PythonError')(
                serializable_error_info_from_exc_info(sys.exc_info())
            )
        )


def _pipeline_or_error_from_repository(graphene_info, repository, selector):
    if not repository.has_pipeline(selector.name):
        return EitherError(
            graphene_info.schema.type_named('PipelineNotFoundError')(pipeline_name=selector.name)
        )
    else:
        orig_pipeline = repository.get_pipeline(selector.name)
        if selector.solid_subset:
            for solid_name in selector.solid_subset:
                if not orig_pipeline.has_solid(solid_name):
                    return EitherError(
                        graphene_info.schema.type_named('SolidNotFoundError')(solid_name=solid_name)
                    )
        pipeline = get_subset_pipeline(orig_pipeline, selector.solid_subset)

        return EitherValue(graphene_info.schema.type_named('Pipeline')(pipeline))


def _pipeline_or_error_from_container(graphene_info, container, selector):
    return _repository_or_error_from_container(graphene_info, container).chain(
        lambda repository: _pipeline_or_error_from_repository(graphene_info, repository, selector)
    )


def _config_or_error_from_pipeline(graphene_info, pipeline, env_config):
    pipeline_env_type = pipeline.get_dagster_pipeline().environment_type
    validated_config = evaluate_config_value(pipeline_env_type, env_config)

    if not validated_config.success:
        return EitherError(
            graphene_info.schema.type_named('PipelineConfigValidationInvalid')(
                pipeline=pipeline,
                errors=[
                    graphene_info.schema.type_named(
                        'PipelineConfigValidationError'
                    ).from_dagster_error(graphene_info, err)
                    for err in validated_config.errors
                ],
            )
        )
    else:
        return EitherValue(validated_config)


MarshalledInput = namedtuple('MarshalledInput', 'input_name key')


class StepExecution(namedtuple('_StepExecution', 'step_key marshalled_inputs marshalled_outputs')):
    def __new__(cls, step_key, marshalled_inputs, marshalled_outputs):
        return super(StepExecution, cls).__new__(
            cls,
            check.str_param(step_key, 'step_key'),
            list(map(lambda inp: MarshalledInput(**inp), marshalled_inputs)),
            list(
                map(
                    lambda out: MarshalledOutput(
                        output_name=out['output_name'], marshalling_key=out['key']
                    ),
                    marshalled_outputs,
                )
            ),
        )


class SubplanExecutionArgs(
    namedtuple(
        '_SubplanExecutionArgs',
        'graphene_info pipeline_name env_config step_executions execution_metadata',
    )
):
    def __new__(cls, graphene_info, pipeline_name, env_config, step_executions, execution_metadata):
        return super(SubplanExecutionArgs, cls).__new__(
            cls,
            graphene_info=check.inst_param(graphene_info, 'graphene_info', ResolveInfo),
            pipeline_name=check.str_param(pipeline_name, 'pipeline_name'),
            env_config=check.opt_dict_param(env_config, 'env_config'),
            step_executions=check.list_param(
                step_executions, 'step_executions', of_type=StepExecution
            ),
            execution_metadata=check.inst_param(
                execution_metadata, 'execution_metadata', ExecutionMetadata
            ),
        )

    @property
    def step_keys(self):
        return [se.step_key for se in self.step_executions]


def start_subplan_execution(args):
    check.inst_param(args, 'args', SubplanExecutionArgs)

    graphene_info = args.graphene_info

    # this is a sequence of validations to valiadate inputs:
    # validate_pipeline => validate_config => validate_execution_plan => execute_execution_plan
    return (
        _pipeline_or_error_from_container(
            graphene_info,
            graphene_info.context.repository_container,
            ExecutionSelector(args.pipeline_name),
        )
        .chain(
            lambda dauphin_pipeline: _chain_config_or_error_from_pipeline(args, dauphin_pipeline)
        )
        .value()
    )


def _chain_config_or_error_from_pipeline(args, dauphin_pipeline):
    return (
        _config_or_error_from_pipeline(args.graphene_info, dauphin_pipeline, args.env_config)
        .chain(
            lambda evaluate_value_result: _execute_marshalling_or_error(
                args, dauphin_pipeline, evaluate_value_result
            )
        )
        .value()
    )


def _execute_marshalling_or_error(args, dauphin_pipeline, evaluate_value_result):
    check.inst_param(args, 'args', SubplanExecutionArgs)
    check.inst_param(dauphin_pipeline, 'dauphin_pipeline', DauphinPipeline)
    check.inst_param(evaluate_value_result, 'evaluate_value_result', EvaluateValueResult)

    try:
        step_events = execute_marshalling(
            dauphin_pipeline.get_dagster_pipeline(),
            step_keys=args.step_keys,
            inputs_to_marshal=_get_inputs_to_marshal(args),
            outputs_to_marshal={se.step_key: se.marshalled_outputs for se in args.step_executions},
            environment_dict=evaluate_value_result.value,
            execution_metadata=args.execution_metadata,
            throw_on_user_error=False,
        )

    except DagsterInvalidSubplanMissingInputError as invalid_subplan_error:
        return EitherError(
            _type_of(args, 'InvalidSubplanMissingInputError')(
                step=DauphinExecutionStep(invalid_subplan_error.step),
                missing_input_name=invalid_subplan_error.input_name,
            )
        )

    except DagsterInvalidSubplanOutputNotFoundError as output_not_found_error:
        return EitherError(
            _type_of(args, 'StartSubplanExecutionInvalidOutputError')(
                step=DauphinExecutionStep(output_not_found_error.step),
                invalid_output_name=output_not_found_error.output_name,
            )
        )

    except DagsterInvalidSubplanInputNotFoundError as input_not_found_error:
        return EitherError(
            _type_of(args, 'StartSubplanExecutionInvalidInputError')(
                step=DauphinExecutionStep(input_not_found_error.step),
                invalid_input_name=input_not_found_error.input_name,
            )
        )

    except DagsterExecutionStepNotFoundError as step_not_found_error:
        return EitherError(
            _type_of(args, 'StartSubplanExecutionInvalidStepError')(
                invalid_step_key=step_not_found_error.step_key
            )
        )

    # https://github.com/dagster-io/dagster/issues/763
    # Once this issue is resolve we should be able to eliminate this
    except DagsterUserCodeExecutionError as ducee:
        return EitherError(
            _type_of(args, 'PythonError')(
                serializable_error_info_from_exc_info(ducee.original_exc_info)
            )
        )

    return _type_of(args, 'StartSubplanExecutionSuccess')(
        pipeline=dauphin_pipeline,
        has_failures=any(se for se in step_events if se.is_step_failure),
        step_events=list(map(_create_dauphin_step_event, step_events)),
    )


def _create_dauphin_step_event(step_event):
    check.inst_param(step_event, 'step_event', ExecutionStepEvent)
    if step_event.is_successful_output:
        return DauphinSuccessfulStepOutputEvent(
            success=step_event.is_successful_output,
            step=DauphinExecutionStep(step_event.step),
            output_name=step_event.success_data.output_name,
            value_repr=repr(step_event.success_data.value),
        )
    elif step_event.is_step_failure:
        return DauphinStepFailureEvent(
            success=step_event.is_successful_output,
            step=DauphinExecutionStep(step_event.step),
            error_message=str(step_event.failure_data.dagster_error),
        )
    else:
        check.failed('{step_event} unsupported'.format(step_event=step_event))


def _type_of(args, type_name):
    return args.graphene_info.schema.type_named(type_name)


def _get_inputs_to_marshal(args):
    inputs_to_marshal = defaultdict(dict)
    for step_execution in args.step_executions:
        for input_name, marshalling_key in step_execution.marshalled_inputs:
            inputs_to_marshal[step_execution.step_key][input_name] = marshalling_key
    return dict(inputs_to_marshal)
