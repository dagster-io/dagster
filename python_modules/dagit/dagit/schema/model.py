from __future__ import absolute_import
import sys
import uuid

from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.evaluator import evaluate_config_value
from dagster.core.execution import create_execution_plan

from dagster.utils.error import serializable_error_info_from_exc_info

from .utils import (
    EitherValue,
    EitherError,
)


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


def get_pipeline(info, name):
    check.inst_param(info, 'info', ResolveInfo)
    return _get_pipeline(info, name).value()


def get_pipeline_or_raise(info, name):
    check.inst_param(info, 'info', ResolveInfo)
    return _get_pipeline(info, name).value_or_raise()


def _get_pipeline(info, name):
    check.inst_param(info, 'info', ResolveInfo)
    check.str_param(name, 'name')
    return _pipeline_or_error_from_container(info, info.context.repository_container, name)


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
        return runs.PipelineRun(run)


def get_runs(info):
    pipeline_run_storage = info.context.pipeline_runs
    return [runs.PipelineRun(run) for run in pipeline_run_storage.all_runs()]


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
        return config_or_error.chain(lambda config: info.schema.type_named('ExecutionPlan')(
            pipeline,
            create_execution_plan(pipeline.get_dagster_pipeline(), config.value),
        ))

    pipeline_or_error = _pipeline_or_error_from_container(
        info, info.context.repository_container, pipelineName
    )
    return pipeline_or_error.chain(create_plan).value()


def start_pipeline_execution(info, pipelineName, config):
    check.inst_param(info, 'info', ResolveInfo)
    check.str_param(pipelineName, 'pipelineName')
    pipeline_run_storage = info.context.pipeline_runs

    def get_config_and_start_execution(pipeline):
        def start_execution(config):
            new_run_id = str(uuid.uuid4())
            execution_plan = create_execution_plan(pipeline.get_dagster_pipeline(), config.value)
            run = pipeline_run_storage.add_run(new_run_id, pipelineName, config, execution_plan)
            info.context.execution_manager.execute_pipeline(
                pipeline.get_dagster_pipeline(), config.value, run
            )
            return info.schema.type_named('StartPipelineExecutionSuccess')(
                run=info.schema.type_named('PipelineRun')(run)
            )

        config_or_error = _config_or_error_from_pipeline(info, pipeline, config)
        return config_or_error.chain(start_execution)

    pipeline_or_error = _pipeline_or_error_from_container(
        info, info.context.repository_container, pipelineName
    )
    return pipeline_or_error.chain(get_config_and_start_execution).value()


def get_pipeline_run_observable(info, runId, after=None):
    check.inst_param(info, 'info', ResolveInfo)
    check.str_param(runId, 'runId')
    check.opt_str_param(after, 'after')
    pipeline_run_storage = info.context.pipeline_runs
    run = pipeline_run_storage.get_run_by_id(runId)
    if not run:
        raise Exception('No run with such id: {run_id}'.format(run_id=runId))

    pipeline_name = run.pipeline_name

    def get_observable(pipeline):
        return run.observable_after_cursor(after).map(
            lambda event: info.schema.type_named('PipelineRunEvent').from_dagster_event(info, event, pipeline)
        )

    return _pipeline_or_error_from_container(
        info,
        info.context.repository_container,
        pipeline_name,
    ).chain(get_observable).value_or_raise()


def _repository_or_error_from_container(info, container):
    error = container.error
    if error != None:
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


def _pipeline_or_error_from_repository(info, repository, pipeline_name):
    if not repository.has_pipeline(pipeline_name):
        return EitherError(
            info.schema.type_named('PipelineNotFoundError')(pipeline_name=pipeline_name)
        )
    else:
        return EitherValue(
            info.schema.type_named('Pipeline')(repository.get_pipeline(pipeline_name))
        )


def _pipeline_or_error_from_container(info, container, pipeline_name):
    return _repository_or_error_from_container(
        info, container
    ).chain(lambda repository: _pipeline_or_error_from_repository(info, repository, pipeline_name))


def _config_or_error_from_pipeline(info, pipeline, config):
    pipeline_env_type = pipeline.get_dagster_pipeline().environment_type
    config_result = evaluate_config_value(pipeline_env_type, config)

    if not config_result.success:
        return EitherError(
            info.schema.type_named('PipelineConfigValidationInvalid')(
                pipeline=pipeline,
                errors=[
                    info.schema.type_named('PipelineConfigValidationError').from_dagster_error(
                        info, err
                    ) for err in config_result.errors
                ],
            )
        )
    else:
        return EitherValue(config_result)
