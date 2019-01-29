from __future__ import absolute_import
from collections import defaultdict, namedtuple
import sys
import uuid


from graphql.execution.base import ResolveInfo

from dagster import check, ExecutionMetadata
from dagster.core.definitions.environment_configs import construct_environment_config
from dagster.core.execution import (
    ExecutionPlan,
    ExecutionSelector,
    create_execution_plan_with_typed_environment,
    execute_externalized_plan,
    get_subset_pipeline,
)
from dagster.core.types.evaluator import evaluate_config_value, EvaluateValueResult

from dagster.utils.error import serializable_error_info_from_exc_info

from .config_types import to_dauphin_config_type
from .pipelines import DauphinPipeline
from .runtime_types import to_dauphin_runtime_type
from .utils import EitherValue, EitherError


def get_pipelines(info):
    check.inst_param(info, 'info', ResolveInfo)
    return _get_pipelines(info).value()


def get_pipelines_or_raise(info):
    check.inst_param(info, 'info', ResolveInfo)
    return _get_pipelines(info).value_or_raise()


def _get_pipelines(info):
    check.inst_param(info, 'info', ResolveInfo)

    def process_pipelines(repository):
        pipeline_instances = []
        for pipeline_def in repository.get_all_pipelines():
            pipeline_instances.append(info.schema.type_named('Pipeline')(pipeline_def))
        return info.schema.type_named('PipelineConnection')(
            nodes=sorted(pipeline_instances, key=lambda pipeline: pipeline.name)
        )

    repository_or_error = _repository_or_error_from_container(
        info, info.context.repository_container
    )
    return repository_or_error.chain(process_pipelines)


def get_pipeline(info, selector):
    return _get_pipeline(info, selector).value()


def get_pipeline_or_raise(info, selector):
    return _get_pipeline(info, selector).value_or_raise()


def _get_pipeline(info, selector):
    check.inst_param(info, 'info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    return _pipeline_or_error_from_container(info, info.context.repository_container, selector)


def get_pipeline_type(info, pipelineName, typeName):
    check.inst_param(info, 'info', ResolveInfo)
    check.str_param(pipelineName, 'pipelineName')
    check.str_param(typeName, 'typeName')
    pipeline_or_error = _pipeline_or_error_from_container(
        info, info.context.repository_container, ExecutionSelector(pipelineName)
    )
    return pipeline_or_error.chain(lambda pip: pip.get_type(info, typeName)).value_or_raise()


def _config_type_or_error(info, dauphin_pipeline, config_type_name):
    pipeline = dauphin_pipeline.get_dagster_pipeline()
    if not pipeline.has_config_type(config_type_name):
        return EitherError(
            info.schema.type_named('ConfigTypeNotFoundError')(
                pipeline=pipeline, config_type_name=config_type_name
            )
        )
    else:
        dauphin_config_type = to_dauphin_config_type(pipeline.config_type_named(config_type_name))
        return EitherValue(dauphin_config_type)


def get_config_type(info, pipeline_name, type_name):
    pipeline_or_error = _pipeline_or_error_from_container(
        info, info.context.repository_container, ExecutionSelector(pipeline_name)
    )

    return pipeline_or_error.chain(
        lambda pipeline: _config_type_or_error(info, pipeline, type_name)
    ).value()


def _runtime_type_or_error(info, dauphin_pipeline, runtime_type_name):
    pipeline = dauphin_pipeline.get_dagster_pipeline()
    if not pipeline.has_runtime_type(runtime_type_name):
        return EitherError(
            info.schema.type_named('RuntimeTypeNotFoundError')(
                pipeline=pipeline, runtime_type_name=runtime_type_name
            )
        )
    else:
        dauphin_runtime_type = to_dauphin_runtime_type(
            pipeline.runtime_type_named(runtime_type_name)
        )
        return EitherValue(dauphin_runtime_type)


def get_runtime_type(info, pipeline_name, type_name):
    pipeline_or_error = _pipeline_or_error_from_container(
        info, info.context.repository_container, ExecutionSelector(pipeline_name)
    )

    return pipeline_or_error.chain(
        lambda pipeline: _runtime_type_or_error(info, pipeline, type_name)
    ).value()


def get_run(info, runId):
    pipeline_run_storage = info.context.pipeline_runs
    run = pipeline_run_storage.get_run_by_id(runId)
    if not run:
        raise Exception('No run with such id: {run_id}'.format(run_id=runId))
    else:
        return info.schema.type_named('PipelineRun')


def get_runs(info):
    pipeline_run_storage = info.context.pipeline_runs
    return [info.schema.type_named('PipelineRun')(run) for run in pipeline_run_storage.all_runs()]


def validate_pipeline_config(info, selector, config):
    check.inst_param(info, 'info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    def do_validation(pipeline):
        config_or_error = _config_or_error_from_pipeline(info, pipeline, config)
        return config_or_error.chain(
            lambda config: info.schema.type_named('PipelineConfigValidationValid')(pipeline)
        )

    pipeline_or_error = _pipeline_or_error_from_container(
        info, info.context.repository_container, selector
    )
    return pipeline_or_error.chain(do_validation).value()


def get_execution_plan(info, selector, config):
    check.inst_param(info, 'info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    def create_plan(pipeline):
        config_or_error = _config_or_error_from_pipeline(info, pipeline, config)
        return config_or_error.chain(
            lambda evaluate_value_result: info.schema.type_named('ExecutionPlan')(
                pipeline,
                create_execution_plan_with_typed_environment(
                    pipeline.get_dagster_pipeline(),
                    construct_environment_config(evaluate_value_result.value),
                    ExecutionMetadata(),
                ),
            )
        )

    pipeline_or_error = _pipeline_or_error_from_container(
        info, info.context.repository_container, selector
    )
    return pipeline_or_error.chain(create_plan).value()


def start_pipeline_execution(info, selector, config):
    check.inst_param(info, 'info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    pipeline_run_storage = info.context.pipeline_runs
    env_config = config

    def get_config_and_start_execution(pipeline):
        def _start_execution(validated_config_either):
            new_run_id = str(uuid.uuid4())
            execution_plan = create_execution_plan_with_typed_environment(
                pipeline.get_dagster_pipeline(),
                construct_environment_config(validated_config_either.value),
                ExecutionMetadata(),
            )
            run = pipeline_run_storage.create_run(new_run_id, selector, env_config, execution_plan)
            pipeline_run_storage.add_run(run)

            info.context.execution_manager.execute_pipeline(
                info.context.repository_container, pipeline.get_dagster_pipeline(), run
            )
            return info.schema.type_named('StartPipelineExecutionSuccess')(
                run=info.schema.type_named('PipelineRun')(run)
            )

        config_or_error = _config_or_error_from_pipeline(info, pipeline, env_config)
        return config_or_error.chain(_start_execution)

    pipeline_or_error = _pipeline_or_error_from_container(
        info, info.context.repository_container, selector
    )
    return pipeline_or_error.chain(get_config_and_start_execution).value()


def get_pipeline_run_observable(info, run_id, after=None):
    check.inst_param(info, 'info', ResolveInfo)
    check.str_param(run_id, 'run_id')
    check.opt_str_param(after, 'after')
    pipeline_run_storage = info.context.pipeline_runs
    run = pipeline_run_storage.get_run_by_id(run_id)
    if not run:
        raise Exception('No run with such id: {run_id}'.format(run_id=run_id))

    def get_observable(pipeline):
        pipeline_run_event_type = info.schema.type_named('PipelineRunEvent')
        return run.observable_after_cursor(after).map(
            lambda events: info.schema.type_named('PipelineRunLogsSubscriptionPayload')(
                messages=[
                    pipeline_run_event_type.from_dagster_event(info, event, pipeline)
                    for event in events
                ]
            )
        )

    return (
        _pipeline_or_error_from_container(info, info.context.repository_container, run.selector)
        .chain(get_observable)
        .value_or_raise()
    )


def _repository_or_error_from_container(info, container):
    error = container.error
    if error is not None:
        return EitherError(
            info.schema.type_named('PythonError')(serializable_error_info_from_exc_info(error))
        )
    try:
        return EitherValue(container.repository)
    except Exception:  # pylint: disable=broad-except
        return EitherError(
            info.schema.type_named('PythonError')(
                serializable_error_info_from_exc_info(sys.exc_info())
            )
        )


def _pipeline_or_error_from_repository(info, repository, selector):
    if not repository.has_pipeline(selector.name):
        return EitherError(
            info.schema.type_named('PipelineNotFoundError')(pipeline_name=selector.name)
        )
    else:
        orig_pipeline = repository.get_pipeline(selector.name)
        if selector.solid_subset:
            for solid_name in selector.solid_subset:
                if not orig_pipeline.has_solid(solid_name):
                    return EitherError(
                        info.schema.type_named('SolidNotFoundError')(solid_name=solid_name)
                    )
        pipeline = get_subset_pipeline(orig_pipeline, selector.solid_subset)

        return EitherValue(info.schema.type_named('Pipeline')(pipeline))


def _pipeline_or_error_from_container(info, container, selector):
    return _repository_or_error_from_container(info, container).chain(
        lambda repository: _pipeline_or_error_from_repository(info, repository, selector)
    )


def _config_or_error_from_pipeline(info, pipeline, env_config):
    pipeline_env_type = pipeline.get_dagster_pipeline().environment_type
    validated_config = evaluate_config_value(pipeline_env_type, env_config)

    if not validated_config.success:
        return EitherError(
            info.schema.type_named('PipelineConfigValidationInvalid')(
                pipeline=pipeline,
                errors=[
                    info.schema.type_named('PipelineConfigValidationError').from_dagster_error(
                        info, err
                    )
                    for err in validated_config.errors
                ],
            )
        )
    else:
        return EitherValue(validated_config)


MarshalledInput = namedtuple('MarshalledInput', 'input_name key')
MarshalledOutput = namedtuple('MarshalledOutput', 'output_name key')


class StepExecution(namedtuple('_StepExecution', 'step_key marshalled_inputs marshalled_outputs')):
    def __new__(cls, step_key, marshalled_inputs, marshalled_outputs):
        return super(StepExecution, cls).__new__(
            cls,
            check.str_param(step_key, 'step_key'),
            list(map(lambda inp: MarshalledInput(**inp), marshalled_inputs)),
            list(map(lambda out: MarshalledOutput(**out), marshalled_outputs)),
        )


class SubplanExecutionArgs(
    namedtuple(
        '_SubplanExecutionArgs', 'info pipeline_name env_config step_executions execution_metadata'
    )
):
    def __new__(cls, info, pipeline_name, env_config, step_executions, execution_metadata):
        return super(SubplanExecutionArgs, cls).__new__(
            cls,
            info=check.inst_param(info, 'info', ResolveInfo),
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

    info = args.info

    # this is a sequence of validations to valiadate inputs:
    # validate_pipeline => validate_config => validate_execution_plan => execute_execution_plan
    return (
        _pipeline_or_error_from_container(
            info, info.context.repository_container, ExecutionSelector(args.pipeline_name)
        )
        .chain(
            lambda dauphin_pipeline: _chain_config_or_error_from_pipeline(args, dauphin_pipeline)
        )
        .value()
    )


def _chain_config_or_error_from_pipeline(args, dauphin_pipeline):
    return (
        _config_or_error_from_pipeline(args.info, dauphin_pipeline, args.env_config)
        .chain(
            lambda evaluate_value_result: _chain_execution_plan_or_error(
                args, dauphin_pipeline, evaluate_value_result
            )
        )
        .value()
    )


def _chain_execution_plan_or_error(args, dauphin_pipeline, evaluate_value_result):
    return (
        _execution_plan_or_error(args, dauphin_pipeline, evaluate_value_result)
        .chain(
            lambda execution_plan: _execute_subplan_or_error(
                args, dauphin_pipeline, execution_plan, evaluate_value_result
            )
        )
        .value()
    )


def _execution_plan_or_error(subplan_execution_args, dauphin_pipeline, evaluate_value_result):
    check.inst_param(subplan_execution_args, 'subplan_execution_args', SubplanExecutionArgs)
    check.inst_param(dauphin_pipeline, 'dauphin_pipeline', DauphinPipeline)
    check.inst_param(evaluate_value_result, 'evaluate_value_result', EvaluateValueResult)

    execution_plan = create_execution_plan_with_typed_environment(
        dauphin_pipeline.get_dagster_pipeline(),
        construct_environment_config(evaluate_value_result.value),
        subplan_execution_args.execution_metadata,
    )

    invalid_keys = []
    for step_key in subplan_execution_args.step_keys:
        if not execution_plan.has_step(step_key):
            invalid_keys.append(step_key)

    if invalid_keys:
        return EitherError(
            subplan_execution_args.info.schema.type_named('StartSubplanExecutionInvalidStepsError')(
                invalid_step_keys=invalid_keys
            )
        )

    else:
        return EitherValue(execution_plan)


def _execute_subplan_or_error(
    subplan_execution_args, dauphin_pipeline, execution_plan, evaluate_value_result
):
    check.inst_param(subplan_execution_args, 'subplan_execution_args', SubplanExecutionArgs)
    check.inst_param(dauphin_pipeline, 'dauphin_pipeline', DauphinPipeline)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(evaluate_value_result, 'evaluate_value_result', EvaluateValueResult)

    inputs_to_marshal = defaultdict(dict)
    outputs_to_marshal = defaultdict(list)

    for step_execution in subplan_execution_args.step_executions:
        step = execution_plan.get_step_by_key(step_execution.step_key)
        for marshalled_input in step_execution.marshalled_inputs:
            if not step.has_step_input(marshalled_input.input_name):
                schema = subplan_execution_args.info.schema
                return EitherError(
                    schema.type_named('StartSubplanExecutionInvalidInputError')(
                        step=schema.type_named('ExecutionStep')(step),
                        invalid_input_name=marshalled_input.input_name,
                    )
                )

            inputs_to_marshal[step.key][marshalled_input.input_name] = marshalled_input.key

        for marshalled_output in step_execution.marshalled_outputs:
            if not step.has_step_output(marshalled_output.output_name):
                schema = subplan_execution_args.info.schema
                return EitherError(
                    schema.type_named('StartSubplanExecutionInvalidOutputError')(
                        step=schema.type_named('ExecutionStep')(step),
                        invalid_output_name=marshalled_output.output_name,
                    )
                )

            outputs_to_marshal[step.key].append(
                {'output': marshalled_output.output_name, 'path': marshalled_output.key}
            )

    _results = execute_externalized_plan(
        pipeline=dauphin_pipeline.get_dagster_pipeline(),
        execution_plan=execution_plan,
        step_keys=subplan_execution_args.step_keys,
        inputs_to_marshal=dict(inputs_to_marshal),
        outputs_to_marshal=outputs_to_marshal,
        environment=evaluate_value_result.value,
        execution_metadata=subplan_execution_args.execution_metadata,
    )

    # TODO: Handle error conditions here

    return subplan_execution_args.info.schema.type_named('StartSubplanExecutionSuccess')(
        pipeline=dauphin_pipeline
    )
