from contextlib import contextmanager
import inspect
import sys
import time

from contextlib2 import ExitStack

from dagster import check
from dagster.core.definitions import PipelineDefinition, create_environment_type
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.definitions.resource import ResourcesBuilder
from dagster.core.errors import (
    DagsterError,
    DagsterUserCodeExecutionError,
    DagsterResourceFunctionError,
    user_code_error_boundary,
)
from dagster.core.events import DagsterEvent, PipelineInitFailureData
from dagster.core.events.log import construct_event_logger
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.intermediates_manager import (
    construct_intermediates_manager,
    IntermediatesManager,
)
from dagster.core.storage.runs import (
    construct_run_storage,
    DagsterRunMeta,
    RunStorage,
    RunStorageMode,
)
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.types.evaluator import (
    EvaluationError,
    evaluate_config_value,
    friendly_string_for_error,
)
from dagster.loggers import default_loggers, default_system_loggers
from dagster.utils import merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info

from .config import RunConfig
from .context.init import InitResourceContext
from .context.system import SystemPipelineExecutionContextData, SystemPipelineExecutionContext
from .context.logger import InitLoggerContext


class PipelineConfigEvaluationError(Exception):
    def __init__(self, pipeline, errors, config_value, *args, **kwargs):
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.errors = check.list_param(errors, 'errors', of_type=EvaluationError)
        self.config_value = config_value

        error_msg = 'Pipeline "{pipeline}" config errors:'.format(pipeline=pipeline.name)

        error_messages = []

        for i_error, error in enumerate(self.errors):
            error_message = friendly_string_for_error(error)
            error_messages.append(error_message)
            error_msg += '\n    Error {i_error}: {error_message}'.format(
                i_error=i_error + 1, error_message=error_message
            )

        self.message = error_msg
        self.error_messages = error_messages

        super(PipelineConfigEvaluationError, self).__init__(error_msg, *args, **kwargs)


def create_environment_config(pipeline, environment_dict=None, mode=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_dict_param(environment_dict, 'environment')
    mode = check.opt_str_param(mode, 'mode', default=pipeline.get_default_mode_name())

    environment_type = create_environment_type(pipeline, mode)

    result = evaluate_config_value(environment_type, environment_dict)

    if not result.success:
        raise PipelineConfigEvaluationError(pipeline, result.errors, environment_dict)

    return EnvironmentConfig.from_dict(result.value)


@contextmanager
def scoped_pipeline_context(pipeline_def, environment_dict, run_config, intermediates_manager=None):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.dict_param(environment_dict, 'environment_dict', key_type=str)
    check.inst_param(run_config, 'run_config', RunConfig)

    environment_config = create_environment_config(
        pipeline_def, environment_dict, mode=run_config.mode
    )

    # The run storage mode will be provided by RunConfig or from the "storage" field in the user's
    # environment config, with preference given to the former if provided.
    storage_mode = run_config.storage_mode or RunStorageMode.from_environment_config(
        environment_config.storage.storage_mode
    )

    intermediates_manager = intermediates_manager or construct_intermediates_manager(
        storage_mode, run_config.run_id, environment_config, pipeline_def
    )

    run_storage = construct_run_storage(storage_mode)

    run_storage.write_dagster_run_meta(
        DagsterRunMeta(
            run_id=run_config.run_id, timestamp=time.time(), pipeline_name=pipeline_def.name
        )
    )

    try:
        loggers = _create_loggers(
            environment_config,
            run_config,
            pipeline_def,
            pipeline_def.get_mode_definition(run_config.mode),
        )
        log_manager = DagsterLogManager(run_id=run_config.run_id, logging_tags={}, loggers=loggers)

        with _create_resources(
            pipeline_def, environment_config, run_config, log_manager
        ) as resources:

            yield construct_pipeline_execution_context(
                run_config,
                pipeline_def,
                resources,
                environment_config,
                run_storage,
                intermediates_manager,
                log_manager,
            )

    except DagsterError as dagster_error:
        user_facing_exc_info = (
            # pylint does not know original_exc_info exists is is_user_code_error is true
            # pylint: disable=no-member
            dagster_error.original_exc_info
            if dagster_error.is_user_code_error
            else sys.exc_info()
        )

        if run_config.executor_config.raise_on_error:
            raise dagster_error

        error_info = serializable_error_info_from_exc_info(user_facing_exc_info)
        yield DagsterEvent.pipeline_init_failure(
            pipeline_name=pipeline_def.name,
            failure_data=PipelineInitFailureData(error=error_info),
            log_manager=_create_context_free_log_manager(run_config, pipeline_def),
        )


def construct_pipeline_execution_context(
    run_config,
    pipeline_def,
    resources,
    environment_config,
    run_storage,
    intermediates_manager,
    log_manager,
):
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(pipeline_def, 'pipeline', PipelineDefinition)
    check.opt_inst_param(resources, 'resources', ResourcesBuilder)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
    check.inst_param(run_storage, 'run_storage', RunStorage)
    check.inst_param(intermediates_manager, 'intermediates_manager', IntermediatesManager)
    check.inst_param(log_manager, 'log_manager', DagsterLogManager)

    logging_tags = get_logging_tags(run_config, pipeline_def)
    log_manager.logging_tags = logging_tags

    return SystemPipelineExecutionContext(
        SystemPipelineExecutionContextData(
            pipeline_def=pipeline_def,
            run_config=run_config,
            resources=resources,
            environment_config=environment_config,
            run_storage=run_storage,
            intermediates_manager=intermediates_manager,
        ),
        logging_tags=logging_tags,
        log_manager=log_manager,
    )


@contextmanager
def _create_resources(pipeline_def, environment_config, run_config, log_manager):
    resources = {}

    mode_definition = pipeline_def.get_mode_definition(run_config.mode)
    # See https://bit.ly/2zIXyqw
    # The "ExitStack" allows one to stack up N context managers and then yield
    # something. We do this so that resources can cleanup after themselves. We
    # can potentially have many resources so we need to use this abstraction.
    with ExitStack() as stack:
        for resource_name, resource_def in sorted(mode_definition.resource_defs.items()):
            user_fn = _create_resource_fn_lambda(
                pipeline_def,
                resource_def,
                environment_config.resources.get(resource_name, {}).get('config'),
                run_config.run_id,
                log_manager,
            )

            resource_obj = stack.enter_context(
                user_code_context_manager(
                    user_fn,
                    DagsterResourceFunctionError,
                    'Error executing resource_fn on ResourceDefinition {name}'.format(
                        name=resource_name
                    ),
                )
            )

            resources[resource_name] = resource_obj
        yield ResourcesBuilder(resources)


def _create_resource_fn_lambda(pipeline_def, resource_def, resource_config, run_id, log_manager):
    return lambda: resource_def.resource_fn(
        InitResourceContext(
            pipeline_def=pipeline_def,
            resource_def=resource_def,
            resource_config=resource_config,
            run_id=run_id,
            log_manager=log_manager,
        )
    )


def _create_loggers(environment_config, run_config, pipeline_def, mode_def):
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(mode_def, 'mode_def', ModeDefinition)

    loggers = []
    for logger_key, logger_def in mode_def.loggers.items() or default_loggers().items():
        if logger_key in environment_config.loggers:
            loggers.append(
                logger_def.logger_fn(
                    InitLoggerContext(
                        environment_config.loggers.get(logger_key, {}).get('config'),
                        pipeline_def,
                        logger_def,
                        run_config.run_id,
                    )
                )
            )

    if run_config.loggers:
        for logger in run_config.loggers:
            loggers.append(logger)

    if not loggers:
        for (logger_def, logger_config) in default_system_loggers():
            loggers.append(
                logger_def.logger_fn(
                    InitLoggerContext(logger_config, pipeline_def, logger_def, run_config.run_id)
                )
            )

    if run_config.event_callback:
        init_logger_context = InitLoggerContext({}, pipeline_def, logger_def, run_config.run_id)
        loggers.append(
            construct_event_logger(run_config.event_callback).logger_fn(init_logger_context)
        )

    return loggers


def _create_context_free_log_manager(run_config, pipeline_def):
    '''In the event of pipeline initialization failure, we want to be able to log the failure
    without a dependency on the ExecutionContext to initialize DagsterLogManager.
    Args:
        run_config (dagster.core.execution_context.RunConfig)
        pipeline_def (dagster.definitions.PipelineDefinition)
    '''
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

    loggers = []
    # Use the default logger
    for (logger_def, logger_config) in default_system_loggers():
        loggers += [
            logger_def.logger_fn(
                InitLoggerContext(logger_config, pipeline_def, logger_def, run_config.run_id)
            )
        ]
    if run_config.event_callback:
        event_logger_def = construct_event_logger(run_config.event_callback)
        loggers += [
            event_logger_def.logger_fn(
                InitLoggerContext({}, pipeline_def, event_logger_def, run_config.run_id)
            )
        ]
    elif run_config.loggers:
        loggers += run_config.loggers

    return DagsterLogManager(run_config.run_id, get_logging_tags(run_config, pipeline_def), loggers)


def _ensure_gen(thing_or_gen):
    if not inspect.isgenerator(thing_or_gen):

        def _gen_thing():
            yield thing_or_gen

        return _gen_thing()

    return thing_or_gen


@contextmanager
def user_code_context_manager(user_fn, error_cls, msg):
    '''Wraps the output of a user provided function that may yield or return a value and
    returns a generator that asserts it only yields a single value.
    '''
    check.callable_param(user_fn, 'user_fn')
    check.subclass_param(error_cls, 'error_cls', DagsterUserCodeExecutionError)

    with user_code_error_boundary(error_cls, msg):
        thing_or_gen = user_fn()
        gen = _ensure_gen(thing_or_gen)

        try:
            thing = next(gen)
        except StopIteration:
            check.failed('Must yield one item. You did not yield anything.')

        yield thing

        stopped = False

        try:
            next(gen)
        except StopIteration:
            stopped = True

        check.invariant(stopped, 'Must yield one item. Yielded more than one item')


def get_logging_tags(run_config, pipeline):
    check.opt_inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    return merge_dicts({'pipeline': pipeline.name}, run_config.tags if run_config else {})
