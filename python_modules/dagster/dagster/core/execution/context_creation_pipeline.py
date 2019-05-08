from contextlib import contextmanager
import inspect
import sys
import time

from contextlib2 import ExitStack

from dagster import check
from dagster.utils import merge_dicts
from dagster.utils.logging import define_colored_console_logger
from dagster.utils.error import serializable_error_info_from_exc_info

from dagster.core.definitions import PipelineDefinition, create_environment_type
from dagster.core.definitions.resource import ResourcesBuilder, ResourcesSource
from dagster.core.definitions.environment_configs import construct_environment_config


from dagster.core.errors import (
    DagsterError,
    DagsterInvariantViolationError,
    DagsterUserCodeExecutionError,
    DagsterContextFunctionError,
    DagsterResourceFunctionError,
    user_code_error_boundary,
)

from dagster.core.events import DagsterEvent, PipelineInitFailureData
from dagster.core.events.logging import construct_event_logger


from dagster.core.intermediates_manager import (
    ObjectStoreIntermediatesManager,
    InMemoryIntermediatesManager,
    IntermediatesManager,
)

from dagster.core.log import DagsterLog

from dagster.core.object_store import FileSystemObjectStore, construct_type_storage_plugin_registry

from dagster.core.runs import (
    DagsterRunMeta,
    FileSystemRunStorage,
    InMemoryRunStorage,
    RunStorage,
    RunStorageMode,
)

from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.types.evaluator import (
    EvaluationError,
    evaluate_config_value,
    friendly_string_for_error,
)

from .execution_context import (
    RunConfig,
    SystemPipelineExecutionContextData,
    SystemPipelineExecutionContext,
)
from .init_context import InitContext, InitResourceContext
from .resource_creation_adapter import ResourceCreationAdapter
from .user_context import ExecutionContext


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
    check.opt_str_param(mode, 'mode')

    environment_type = create_environment_type(pipeline, mode)

    result = evaluate_config_value(environment_type, environment_dict)

    if not result.success:
        raise PipelineConfigEvaluationError(pipeline, result.errors, environment_dict)

    return construct_environment_config(result.value)


def construct_run_storage(run_config, environment_config):
    '''
    Construct the run storage for this pipeline. Our rules are the following:

    If the RunConfig has a storage_mode provided, we use that.

    Then we fallback to environment config.

    If there is no config, we default to in memory storage. This is mostly so
    that tests default to in-memory.
    '''
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)

    if run_config.storage_mode:
        if run_config.storage_mode == RunStorageMode.FILESYSTEM:
            return FileSystemRunStorage()
        elif run_config.storage_mode == RunStorageMode.IN_MEMORY:
            return InMemoryRunStorage()
        elif run_config.storage_mode == RunStorageMode.S3:
            # TODO: Revisit whether we want to use S3 run storage
            return FileSystemRunStorage()
        else:
            check.failed('Unexpected enum {}'.format(run_config.storage_mode))
    elif environment_config.storage.storage_mode == 'filesystem':
        return FileSystemRunStorage()
    elif environment_config.storage.storage_mode == 'in_memory':
        return InMemoryRunStorage()
    elif environment_config.storage.storage_mode == 's3':
        # TODO: Revisit whether we want to use S3 run storage
        return FileSystemRunStorage()
    elif environment_config.storage.storage_mode is None:
        return InMemoryRunStorage()
    else:
        raise DagsterInvariantViolationError(
            'Invalid storage specified {}'.format(environment_config.storage.storage_mode)
        )


@contextmanager
def scoped_pipeline_context(pipeline_def, environment_config, run_config, intermediates_manager):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(intermediates_manager, 'intermediates_manager', IntermediatesManager)

    run_storage = construct_run_storage(run_config, environment_config)

    run_storage.write_dagster_run_meta(
        DagsterRunMeta(
            run_id=run_config.run_id, timestamp=time.time(), pipeline_name=pipeline_def.name
        )
    )

    init_context = InitContext(
        context_config=environment_config.context.config if environment_config.context else {},
        pipeline_def=pipeline_def,
        run_id=run_config.run_id,
    )

    try:

        context_definition = (
            pipeline_def.context_definitions[environment_config.context.name]
            if environment_config.context
            else None
        )

        import logging

        with user_code_context_manager(
            lambda: (
                context_definition.context_fn(init_context)
                if context_definition
                # hardcoded default for now until we have top-level logging as well
                else ExecutionContext.console_logging(logging.INFO)
            ),
            DagsterContextFunctionError,
            'Error executing context_fn on ContextDefinition {name}'.format(
                name=environment_config.context.name if environment_config.context else 'NOCONTEXT'
            ),
        ) as execution_context:
            check.inst(execution_context, ExecutionContext)

            resource_creation_adapter = ResourceCreationAdapter(
                execution_context=execution_context,
                context_definition=context_definition,
                mode_definition=pipeline_def.get_mode_definition(run_config.mode),
                environment_config=environment_config,
            )

            with _create_resources(
                pipeline_def, resource_creation_adapter, environment_config, run_config.run_id
            ) as resources:

                yield construct_pipeline_execution_context(
                    run_config,
                    execution_context,
                    pipeline_def,
                    resources,
                    environment_config,
                    run_storage,
                    intermediates_manager,
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
            log=_create_context_free_log(run_config, pipeline_def),
        )


@contextmanager
def yield_pipeline_execution_context(pipeline_def, environment_dict, run_config):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.dict_param(environment_dict, 'environment_dict', key_type=str)
    check.inst_param(run_config, 'run_config', RunConfig)

    environment_config = create_environment_config(pipeline_def, environment_dict)
    intermediates_manager = construct_intermediates_manager(
        run_config, environment_config, pipeline_def
    )
    with scoped_pipeline_context(
        pipeline_def, environment_config, run_config, intermediates_manager
    ) as context:
        yield context


def construct_pipeline_execution_context(
    run_config,
    execution_context,
    pipeline,
    resources,
    environment_config,
    run_storage,
    intermediates_manager,
):
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(execution_context, 'execution_context', ExecutionContext)
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_inst_param(resources, 'resources', ResourcesBuilder)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
    check.inst_param(run_storage, 'run_storage', RunStorage)
    check.inst_param(intermediates_manager, 'intermediates_manager', IntermediatesManager)

    loggers = _create_loggers(run_config, execution_context)
    logging_tags = get_logging_tags(execution_context, run_config, pipeline)
    log = DagsterLog(run_config.run_id, logging_tags, loggers)

    return SystemPipelineExecutionContext(
        SystemPipelineExecutionContextData(
            pipeline_def=pipeline,
            run_config=run_config,
            resources=resources,
            environment_config=environment_config,
            run_storage=run_storage,
            intermediates_manager=intermediates_manager,
        ),
        logging_tags=logging_tags,
        log=log,
    )


@contextmanager
def _create_resources(pipeline_def, resource_creation_adapter, environment, run_id):
    check.inst_param(
        resource_creation_adapter, 'resource_creation_adapter', ResourceCreationAdapter
    )

    if resource_creation_adapter.is_resource_override:
        yield ResourcesBuilder(
            resource_creation_adapter.get_override_resources(),
            ResourcesSource.CUSTOM_EXECUTION_CONTEXT,
        )
        return

    resources = {}

    # See https://bit.ly/2zIXyqw
    # The "ExitStack" allows one to stack up N context managers and then yield
    # something. We do this so that resources can cleanup after themselves. We
    # can potentially have many resources so we need to use this abstraction.
    with ExitStack() as stack:
        for resource_name, resource_def in resource_creation_adapter.resource_defs.items():
            user_fn = _create_resource_fn_lambda(
                pipeline_def,
                resource_def,
                resource_creation_adapter.get_resource_config(resource_name),
                environment,
                run_id,
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
        yield ResourcesBuilder(resources, ResourcesSource.PIPELINE_CONTEXT_DEF)


def _create_resource_fn_lambda(pipeline_def, resource_def, resource_config, environment, run_id):
    return lambda: resource_def.resource_fn(
        InitResourceContext(
            pipeline_def=pipeline_def,
            resource_def=resource_def,
            context_config=environment.context.config if environment.context else None,
            resource_config=resource_config,
            run_id=run_id,
        )
    )


def ensure_dagster_aws_requirements():
    try:
        import dagster_aws
    except (ImportError, ModuleNotFoundError):
        raise check.CheckError(
            'dagster_aws must be available for import in order to make use of an S3ObjectStore'
        )

    return dagster_aws


def construct_intermediates_manager(run_config, environment_config, pipeline_def):
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

    if run_config.storage_mode:
        if run_config.storage_mode == RunStorageMode.FILESYSTEM:
            return ObjectStoreIntermediatesManager(
                FileSystemObjectStore(
                    run_config.run_id,
                    construct_type_storage_plugin_registry(pipeline_def, RunStorageMode.FILESYSTEM),
                )
            )
        elif run_config.storage_mode == RunStorageMode.IN_MEMORY:
            return InMemoryIntermediatesManager()
        elif run_config.storage_mode == RunStorageMode.S3:
            _dagster_aws = ensure_dagster_aws_requirements()
            from dagster_aws.s3.object_store import S3ObjectStore

            return ObjectStoreIntermediatesManager(
                S3ObjectStore(
                    environment_config.storage.storage_config['s3_bucket'],
                    run_config.run_id,
                    construct_type_storage_plugin_registry(pipeline_def, RunStorageMode.S3),
                )
            )
        else:
            check.failed('Unexpected enum {}'.format(run_config.storage_mode))
    elif environment_config.storage.storage_mode == 'filesystem':
        return ObjectStoreIntermediatesManager(
            FileSystemObjectStore(
                run_config.run_id,
                construct_type_storage_plugin_registry(pipeline_def, RunStorageMode.FILESYSTEM),
            )
        )
    elif environment_config.storage.storage_mode == 'in_memory':
        return InMemoryIntermediatesManager()
    elif environment_config.storage.storage_mode == 's3':
        _dagster_aws = ensure_dagster_aws_requirements()
        from dagster_aws.s3.object_store import S3ObjectStore

        return ObjectStoreIntermediatesManager(
            S3ObjectStore(
                environment_config.storage.storage_config['s3_bucket'],
                run_config.run_id,
                construct_type_storage_plugin_registry(pipeline_def, RunStorageMode.S3),
            )
        )
    elif environment_config.storage.storage_mode is None:
        return InMemoryIntermediatesManager()
    else:
        raise DagsterInvariantViolationError(
            'Invalid storage specified {}'.format(environment_config.storage.storage_mode)
        )


def _create_loggers(run_config, execution_context):
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(execution_context, 'execution_context', ExecutionContext)

    if run_config.event_callback:
        return execution_context.loggers + [construct_event_logger(run_config.event_callback)]
    elif run_config.loggers:
        return execution_context.loggers + run_config.loggers
    else:
        return execution_context.loggers


def _create_context_free_log(run_config, pipeline_def):
    '''In the event of pipeline initialization failure, we want to be able to log the failure
    without a dependency on the ExecutionContext to initialize DagsterLog
    '''
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

    # Use the default logger
    loggers = [define_colored_console_logger('dagster')]
    if run_config.event_callback:
        loggers += [construct_event_logger(run_config.event_callback)]
    elif run_config.loggers:
        loggers += run_config.loggers

    return DagsterLog(run_config.run_id, get_logging_tags(None, run_config, pipeline_def), loggers)


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


def get_logging_tags(user_context_params, run_config, pipeline):
    check.opt_inst_param(user_context_params, 'user_context_params', ExecutionContext)
    check.opt_inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    user_tags = user_context_params.tags if user_context_params else {}
    run_tags = run_config.tags if run_config else {}

    base_tags = merge_dicts({'pipeline': pipeline.name}, user_tags)

    if run_config and run_config.tags:
        user_keys = set(user_tags.keys())
        provided_keys = set(run_tags.keys())
        if not user_keys.isdisjoint(provided_keys):
            raise DagsterInvariantViolationError(
                (
                    'You have specified tags and user-defined tags '
                    'that overlap. User keys: {user_keys}. Reentrant keys: '
                    '{provided_keys}.'
                ).format(user_keys=user_keys, provided_keys=provided_keys)
            )

        return merge_dicts(base_tags, run_tags)
    else:
        return base_tags
