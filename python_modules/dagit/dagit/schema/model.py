import sys
import uuid
import gevent
from dagster import (
    execute_pipeline,
    ReentrantInfo,
    check,
)
from dagster.core.evaluator import evaluate_config_value
from dagster.core.execution import create_execution_plan

from . import pipelines, execution, errors, runs
from .utils import non_null_list, EitherValue, EitherError
from .context import DagsterGraphQLContext


def get_pipelines(context):
    return _get_pipelines(context).value()


def get_pipelines_or_raise(context):
    return _get_pipelines(context).value_or_raise()


def _get_pipelines(context):
    check.inst_param(context, 'context', DagsterGraphQLContext)

    def process_pipelines(repository):
        pipeline_instances = []
        for pipeline_def in repository.get_all_pipelines():
            pipeline_instances.append(pipelines.Pipeline(pipeline_def))
        return pipelines.PipelineConnection(nodes=pipeline_instances)

    repository_or_error = _repository_or_error_from_container(context.repository_container)
    return repository_or_error.chain(process_pipelines)


def get_pipeline(context, name):
    return _get_pipeline(context, name).value()


def get_pipeline_or_raise(context, name):
    return _get_pipeline(context, name).value_or_raise()


def _get_pipeline(context, name):
    check.inst_param(context, 'context', DagsterGraphQLContext)
    check.str_param(name, 'name')
    return _pipeline_or_error_from_container(context.repository_container, name)


def get_pipeline_type(context, pipelineName, typeName):
    check.inst_param(context, 'context', DagsterGraphQLContext)
    check.str_param(pipelineName, 'pipelineName')
    check.str_param(typeName, 'typeName')
    pipeline_or_error = _pipeline_or_error_from_container(
        context.repository_container, pipelineName
    )
    return pipeline_or_error.chain(lambda pip: pip.get_type(typeName)).value_or_raise()


def get_run(context, runId):
    pipeline_run_storage = context.pipeline_runs
    run = pipeline_run_storage.get_run_by_id(runId)
    if not run:
        raise Exception('No run with such id: {run_id}'.format(run_id=runId))
    else:
        return runs.PipelineRun(run)


def get_runs(context):
    pipeline_run_storage = context.pipeline_runs
    return [runs.PipelineRun(run) for run in pipeline_run_storage.all_runs()]


def validate_pipeline_config(context, pipelineName, config):
    check.inst_param(context, 'context', DagsterGraphQLContext)
    check.str_param(pipelineName, 'pipelineName')

    def do_validation(pipeline):
        config_or_error = _config_or_error_from_pipeline(pipeline, config)
        return config_or_error.chain(lambda config: errors.PipelineConfigValidationValid(pipeline))

    pipeline_or_error = _pipeline_or_error_from_container(
        context.repository_container, pipelineName
    )
    return pipeline_or_error.chain(do_validation).value()


def get_execution_plan(context, pipelineName, config):
    check.inst_param(context, 'context', DagsterGraphQLContext)
    check.str_param(pipelineName, 'pipelineName')

    def create_plan(pipeline):
        config_or_error = _config_or_error_from_pipeline(pipeline, config)
        return config_or_error.chain(lambda config: execution.ExecutionPlan(
            pipeline,
            create_execution_plan(pipeline.get_dagster_pipeline(), config.value),
        ))

    pipeline_or_error = _pipeline_or_error_from_container(
        context.repository_container, pipelineName
    )
    return pipeline_or_error.chain(create_plan).value()


def start_pipeline_execution(context, pipelineName, config):
    check.inst_param(context, 'context', DagsterGraphQLContext)
    check.str_param(pipelineName, 'pipelineName')
    pipeline_run_storage = context.pipeline_runs

    def get_config_and_start_execution(pipeline):
        def start_execution(config):
            new_run_id = str(uuid.uuid4())
            execution_plan = create_execution_plan(pipeline.get_dagster_pipeline(), config.value)
            run = pipeline_run_storage.add_run(new_run_id, pipelineName, config, execution_plan)
            gevent.spawn(
                execute_pipeline,
                pipeline.get_dagster_pipeline(),
                config.value,
                reentrant_info=ReentrantInfo(
                    new_run_id,
                    event_callback=run.handle_new_event,
                ),
            )
            return errors.StartPipelineExecutionSuccess(run=runs.PipelineRun(run))

        config_or_error = _config_or_error_from_pipeline(pipeline, config)
        return config_or_error.chain(start_execution)

    pipeline_or_error = _pipeline_or_error_from_container(
        context.repository_container, pipelineName
    )
    return pipeline_or_error.chain(get_config_and_start_execution).value()


def get_pipeline_run_observable(context, runId, after=None):
    check.inst_param(context, 'context', DagsterGraphQLContext)
    check.str_param(runId, 'runId')
    check.opt_str_param(after, 'after')
    pipeline_run_storage = context.pipeline_runs
    run = pipeline_run_storage.get_run_by_id(runId)
    if not run:
        raise Exception('No run with such id: {run_id}'.format(run_id=runId))

    pipeline_name = run.pipeline_name

    def get_observable(pipeline):
        return run.observable_after_cursor(after).map(
            lambda event: runs.PipelineRunEvent.from_dagster_event(context, event, pipeline)
        )

    return _pipeline_or_error_from_container(context.repository_container,
                                             pipeline_name).chain(get_observable).value_or_raise()


def _repository_or_error_from_container(container):
    error = container.error
    if error != None:
        return EitherError(errors.PythonError(*error))
    try:
        return EitherValue(container.repository)
    except Exception:  # pylint: disable=broad-except
        return EitherError(errors.PythonError(*sys.exc_info()))


def _pipeline_or_error_from_repository(repository, pipeline_name):
    if not repository.has_pipeline(pipeline_name):
        return EitherError(errors.PipelineNotFoundError(pipeline_name=pipeline_name))
    else:
        return EitherValue(pipelines.Pipeline(repository.get_pipeline(pipeline_name)))


def _pipeline_or_error_from_container(container, pipeline_name):
    return _repository_or_error_from_container(container).chain(
        lambda repository: _pipeline_or_error_from_repository(repository, pipeline_name)
    )


def _config_or_error_from_pipeline(pipeline, config):
    pipeline_env_type = pipeline.get_dagster_pipeline().environment_type
    config_result = evaluate_config_value(pipeline_env_type, config)

    if not config_result.success:
        return EitherError(
            errors.PipelineConfigValidationInvalid(
                pipeline=pipeline,
                errors=[
                    errors.ConfigErrorData.from_dagster_error(err) for err in config_result.errors
                ],
            )
        )
    else:
        return EitherValue(config_result)
