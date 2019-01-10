from __future__ import absolute_import
import sys
import uuid

from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.types.evaluator import evaluate_config_value
from dagster.core.system_config.types import construct_environment_config
from dagster.core.execution import create_execution_plan_with_typed_environment, get_subset_pipeline

from dagster.utils.error import serializable_error_info_from_exc_info

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
        return info.schema.type_named('PipelineConnection')(nodes=pipeline_instances)

    repository_or_error = _repository_or_error_from_container(
        info, info.context.repository_container
    )
    return repository_or_error.chain(process_pipelines)


def get_pipeline(info, name, solid_subset):
    check.inst_param(info, 'info', ResolveInfo)
    return _get_pipeline(info, name, solid_subset).value()


def get_pipeline_or_raise(info, name, solid_subset=None):
    check.inst_param(info, 'info', ResolveInfo)
    return _get_pipeline(info, name, solid_subset).value_or_raise()


def _get_pipeline(info, name, solid_subset):
    check.inst_param(info, 'info', ResolveInfo)
    check.str_param(name, 'name')
    check.opt_list_param(solid_subset, 'solid_subset', of_type=str)
    return _pipeline_or_error_from_container(
        info, info.context.repository_container, name, solid_subset
    )


def get_pipeline_type(info, pipelineName, typeName):
    check.inst_param(info, 'info', ResolveInfo)
    check.str_param(pipelineName, 'pipelineName')
    check.str_param(typeName, 'typeName')
    pipeline_or_error = _pipeline_or_error_from_container(
        info, info.context.repository_container, pipelineName
    )
    return pipeline_or_error.chain(lambda pip: pip.get_type(info, typeName)).value_or_raise()


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


def validate_pipeline_config(info, pipelineName, config):
    check.inst_param(info, 'info', ResolveInfo)
    check.str_param(pipelineName, 'pipelineName')

    def do_validation(pipeline):
        config_or_error = _config_or_error_from_pipeline(info, pipeline, config)
        return config_or_error.chain(
            lambda config: info.schema.type_named('PipelineConfigValidationValid')(pipeline)
        )

    pipeline_or_error = _pipeline_or_error_from_container(
        info, info.context.repository_container, pipelineName
    )
    return pipeline_or_error.chain(do_validation).value()


def get_execution_plan(info, pipelineName, config):
    check.inst_param(info, 'info', ResolveInfo)
    check.str_param(pipelineName, 'pipelineName')

    def create_plan(pipeline):
        config_or_error = _config_or_error_from_pipeline(info, pipeline, config)
        return config_or_error.chain(
            lambda validated_config_either: info.schema.type_named('ExecutionPlan')(
                pipeline,
                create_execution_plan_with_typed_environment(
                    pipeline.get_dagster_pipeline(),
                    construct_environment_config(validated_config_either.value),
                ),
            )
        )

    pipeline_or_error = _pipeline_or_error_from_container(
        info, info.context.repository_container, pipelineName
    )
    return pipeline_or_error.chain(create_plan).value()


def start_pipeline_execution(info, pipelineName, config):
    check.inst_param(info, 'info', ResolveInfo)
    check.str_param(pipelineName, 'pipelineName')
    pipeline_run_storage = info.context.pipeline_runs
    env_config = config

    def get_config_and_start_execution(pipeline):
        def start_execution(validated_config_either):
            new_run_id = str(uuid.uuid4())
            execution_plan = create_execution_plan_with_typed_environment(
                pipeline.get_dagster_pipeline(),
                construct_environment_config(validated_config_either.value),
            )
            run = pipeline_run_storage.create_run(
                new_run_id, pipelineName, env_config, execution_plan
            )
            pipeline_run_storage.add_run(run)
            info.context.execution_manager.execute_pipeline(
                info.context.repository_container, pipeline.get_dagster_pipeline(), run
            )
            return info.schema.type_named('StartPipelineExecutionSuccess')(
                run=info.schema.type_named('PipelineRun')(run)
            )

        config_or_error = _config_or_error_from_pipeline(info, pipeline, env_config)
        return config_or_error.chain(start_execution)

    pipeline_or_error = _pipeline_or_error_from_container(
        info, info.context.repository_container, pipelineName
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

    pipeline_name = run.pipeline_name

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
        _pipeline_or_error_from_container(
            info, info.context.repository_container, pipeline_name, solid_subset=None
        )
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


def _pipeline_or_error_from_repository(info, repository, pipeline_name, solid_subset):
    if not repository.has_pipeline(pipeline_name):
        return EitherError(
            info.schema.type_named('PipelineNotFoundError')(pipeline_name=pipeline_name)
        )
    else:
        orig_pipeline = repository.get_pipeline(pipeline_name)
        if solid_subset is not None:
            for solid_name in solid_subset:
                if not orig_pipeline.has_solid(solid_name):
                    return EitherError(
                        info.schema.type_named('SolidNotFoundError')(solid_name=solid_name)
                    )
        pipeline = get_subset_pipeline(orig_pipeline, solid_subset)

        return EitherValue(info.schema.type_named('Pipeline')(pipeline))


def _pipeline_or_error_from_container(info, container, pipeline_name, solid_subset=None):
    return _repository_or_error_from_container(info, container).chain(
        lambda repository: _pipeline_or_error_from_repository(
            info, repository, pipeline_name, solid_subset
        )
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
