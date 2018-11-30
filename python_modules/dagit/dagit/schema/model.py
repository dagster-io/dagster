from dagster import (
    execute_pipeline,
    ReentrantInfo,
    check,
)
from dagster.core.evaluator import evaluate_config_value
from dagster.core.execution import create_execution_plan

from . import pipeline, execution, errors, run
from .utils import non_null_list, SomethingOrError
from .context import DagsterGraphQLContext


def get_pipelines(context):
    check.inst_param(context, 'context', DagsterGraphQLContext)

    def process_pipelines(repository):
        pipelines = []
        for pipeline_def in repository.get_all_pipelines():
            pipelines.append(pipeline.Pipeline(pipeline_def))
        return pipeline.PipelineConnection(nodes=pipelines)

    repository_or_error = _repository_or_error_from_container(context.repository_container)
    return repository_or_error.chain(process_pipelines).get()


def get_pipeline(context, name):
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
    return pipeline_or_error.chain(lambda pipeline: pipeline.get_type(typeName)).get()


def validate_pipeline_config(context, pipelineName, config):
    check.inst_param(context, 'context', DagsterGraphQLContext)
    check.str_param(pipelineName, 'pipelineName')
    check.dict_param(config, 'config')

    def do_validation(pipeline):
        config_or_error = _repository_or_error_from_container(pipeline, config)
        return config.chain(lambda config: PipelineConfigValidationValid(pipeline))

    pipeline_or_error = _pipeline_or_error_from_container(
        context.repository_container, pipelineName
    )
    return pipeline_or_error.chain(do_validation).get()


def get_execution_plan(context, pipelineName, config):
    check.inst_param(context, 'context', DagsterGraphQLContext)
    check.str_param(pipelineName, 'pipelineName')
    check.dict_param(config, 'config')

    def create_plan(pipeline):
        config_or_error = _config_or_error_from_pipeline(pipeline, config)
        return config.chain(lambda config: execution.ExecutionPlan(
            pipeline,
            create_execution_plan(pipeline._pipeline, config.value),
        ))

    pipeline_or_error = _pipeline_or_error_from_container(
        context.repository_container, pipelineName
    )
    return pipeline_or_error.chain(create_plan).get()


def start_pipeline_execution(context, pipelineName, config):
    check.inst_param(context, 'context', DagsterGraphQLContext)
    check.str_param(pipelineName, 'pipelineName')
    check.dict_param(config, 'config')
    pipeline_run_storage = context.context.pipeline_runs

    def _start_execution(pipeline):
        new_run_id = str(uuid.uuid4())
        run = pipeline_run_storage.add_run(new_run_id, pipelineName, config)
        gevent.spawn(
            execute_pipeline,
            pipeline._pipeline,
            config,
            reentrant_info=ReentrantInfo(
                runId,
                event_callback=run.handle_new_event,
            ),
        )
        return StartPipelineExecutionSuccess(
            run=run.PipelineRun(runId=new_run_id, pipeline=pipeline.Pipeline(pipeline))
        )

    return _pipeline_or_error_from_container(context.repository_container,
                                             pipelineName).chain(_start_execution).get()


def get_pipeline_run_observable(context, runId, after=None):
    check.inst_param(context, 'context', DagsterGraphQLContext)
    check.str_param(runId, 'runId')
    check.opt_str_param(after, 'after')
    pipeline_run_storage = context.context.pipeline_runs
    run = pipeline_run_storage.get_run_by_id(runId)
    if run:
        return run.observable_after_cursor(after).map(
            lambda event: run.PipelineRunEvent.from_dagster_event(event, pipeline)
        )
    else:
        raise Exception('No run with such id: {run_id}'.format(run_id=runId))


def _repository_or_error_from_container(container):
    error = container.error
    if error != None:
        result = errors.PythonError(*error)
    try:
        result = container.repository
    except Exception:  # pylint: disable=broad-except
        result = errors.PythonError(*sys.exc_info())

    return SomethingOrError(result, lambda repo: isinstance(repo, errors.PythonError))


def _pipeline_or_error_from_repository(repository, pipeline_name):
    if not repository.has_pipeline(pipeline_name):
        result = errors.PipelineNotFoundError(pipeline_name=pipeline_name)
    else:
        result = pipeline.Pipeline(repository.get_pipeline(pipeline_name))
    return SomethingOrError(result, lambda pip: not isinstance(pip, pipeline.Pipeline))


def _pipeline_or_error_from_container(container, pipeline_name):
    return _repository_or_error_from_container(container).chain(
        lambda repository: _pipeline_or_error_from_repository(repository, pipeline_name)
    )


def _config_or_error_from_pipeline(pipeline, config):
    pipeline_env_type = pipeline.environment_type
    config_result = evaluate_config_value(pipeline_env_type, config)

    if not config_result.success:
        result = errors.PipelineConfigValidationInvalid(
            pipeline=pipeline.Pipeline(pipeline),
            errors=map(create_graphql_error, config_result.errors),
        )
    else:
        result = config_result

    return SomethingOrError(
        result, lambda config: isinstance(config_result, PipelineConfigValidationInvalid)
    )
