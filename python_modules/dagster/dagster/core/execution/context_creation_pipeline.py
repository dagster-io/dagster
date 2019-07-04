from collections import namedtuple
from contextlib import contextmanager
import inspect
import sys
import time

from contextlib2 import ExitStack

from dagster import check
from dagster.core.definitions import PipelineDefinition, create_environment_type
from dagster.core.definitions.handle import ExecutionTargetHandle
from dagster.core.definitions.resource import ScopedResourcesBuilder
from dagster.core.definitions.system_storage import SystemStorageData
from dagster.core.errors import (
    DagsterError,
    DagsterInvariantViolationError,
    DagsterUserCodeExecutionError,
    DagsterResourceFunctionError,
    DagsterInvalidConfigError,
    user_code_error_boundary,
)
from dagster.core.events import DagsterEvent, PipelineInitFailureData
from dagster.core.events.log import construct_event_logger
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.init import InitSystemStorageContext
from dagster.core.storage.runs import DagsterRunMeta
from dagster.core.storage.type_storage import construct_type_storage_plugin_registry
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.types.evaluator import evaluate_config
from dagster.loggers import default_loggers, default_system_loggers
from dagster.utils import merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info

from .config import RunConfig
from .context.init import InitResourceContext
from .context.system import SystemPipelineExecutionContextData, SystemPipelineExecutionContext
from .context.logger import InitLoggerContext


def create_environment_config(pipeline, environment_dict=None, run_config=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_dict_param(environment_dict, 'environment')
    run_config = check.opt_inst_param(run_config, 'run_config', RunConfig, default=RunConfig())

    mode = run_config.mode or pipeline.get_default_mode_name()
    environment_type = create_environment_type(pipeline, mode)

    result = evaluate_config(environment_type, environment_dict, pipeline, run_config)

    if not result.success:
        raise DagsterInvalidConfigError(pipeline, result.errors, environment_dict)

    return EnvironmentConfig.from_dict(result.value)


@contextmanager
def create_resource_builder(pipeline_def, environment_config, run_config, log_manager):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(log_manager, 'log_manager', DagsterLogManager)

    resources_stack = ResourcesStack(pipeline_def, environment_config, run_config, log_manager)
    yield resources_stack.create()
    resources_stack.teardown()


def construct_system_storage_data(storage_init_context):
    return storage_init_context.system_storage_def.system_storage_creation_fn(storage_init_context)


def system_storage_def_from_config(mode_definition, environment_config):
    for system_storage_def in mode_definition.system_storage_defs:
        if system_storage_def.name == environment_config.storage.system_storage_name:
            return system_storage_def

    check.failed(
        'Could not find storage mode {}. Should have be caught by config system'.format(
            environment_config.storage.system_storage_name
        )
    )


def check_persistent_storage_requirement(pipeline_def, system_storage_def, run_config):
    if (
        run_config.executor_config.requires_persistent_storage
        and not system_storage_def.is_persistent
    ):
        raise DagsterInvariantViolationError(
            (
                'While invoking pipeline {pipeline_name}. You have attempted '
                'to use the multiprocessing executor while using system '
                'storage {storage_name} which does not persist intermediates. '
                'This means there would be no way to move data between different '
                'processes. Please configure your pipeline in the storage config '
                'section to use persistent system storage such as the filesystem.'
            ).format(pipeline_name=pipeline_def.name, storage_name=system_storage_def.name)
        )


# This represents all the data that is passed *into* context creation process.
# The remainder of the objects generated (e.g. loggers, resources) are created
# using user-defined code that may fail at runtime and result in the emission
# of a pipeline init failure events. The data in this object are passed all
# over the place during the context creation process so grouping here for
# ease of argument passing etc.
ContextCreationData = namedtuple(
    'ContextCreationData',
    'pipeline_def environment_config run_config mode_def system_storage_def execution_target_handle',
)


def create_context_creation_data(pipeline_def, environment_dict, run_config):
    environment_config = create_environment_config(pipeline_def, environment_dict, run_config)

    mode_def = pipeline_def.get_mode_definition(run_config.mode)
    system_storage_def = system_storage_def_from_config(mode_def, environment_config)

    check_persistent_storage_requirement(pipeline_def, system_storage_def, run_config)

    return ContextCreationData(
        pipeline_def=pipeline_def,
        environment_config=environment_config,
        run_config=run_config,
        mode_def=mode_def,
        system_storage_def=system_storage_def,
        execution_target_handle=ExecutionTargetHandle.get_handle(pipeline_def),
    )


@contextmanager
def scoped_pipeline_context(
    pipeline_def,
    environment_dict,
    run_config,
    system_storage_data=None,
    scoped_resources_builder_cm=create_resource_builder,
):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.dict_param(environment_dict, 'environment_dict', key_type=str)
    check.inst_param(run_config, 'run_config', RunConfig)
    check.opt_inst_param(system_storage_data, 'system_storage_data', SystemStorageData)

    context_creation_data = create_context_creation_data(pipeline_def, environment_dict, run_config)

    # After this try block, a Dagster exception thrown will result in a pipeline init failure event.
    try:
        log_manager = create_log_manager(context_creation_data)

        with scoped_resources_builder_cm(
            context_creation_data.pipeline_def,
            context_creation_data.environment_config,
            context_creation_data.run_config,
            log_manager,
        ) as scoped_resources_builder:

            system_storage_data = create_system_storage_data(
                context_creation_data, system_storage_data, scoped_resources_builder
            )

            yield construct_pipeline_execution_context(
                context_creation_data=context_creation_data,
                scoped_resources_builder=scoped_resources_builder,
                system_storage_data=system_storage_data,
                log_manager=log_manager,
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


def create_system_storage_data(
    context_creation_data, system_storage_data, scoped_resources_builder
):
    check.inst_param(context_creation_data, 'context_creation_data', ContextCreationData)

    environment_config, pipeline_def, system_storage_def, run_config = (
        context_creation_data.environment_config,
        context_creation_data.pipeline_def,
        context_creation_data.system_storage_def,
        context_creation_data.run_config,
    )

    system_storage_data = (
        system_storage_data
        if system_storage_data
        else construct_system_storage_data(
            InitSystemStorageContext(
                pipeline_def=pipeline_def,
                mode_def=context_creation_data.mode_def,
                system_storage_def=system_storage_def,
                system_storage_config=environment_config.storage.system_storage_config,
                run_config=run_config,
                environment_config=environment_config,
                type_storage_plugin_registry=construct_type_storage_plugin_registry(
                    pipeline_def, system_storage_def
                ),
                resources=scoped_resources_builder.build(
                    # currently provide default for resource mapping
                    lambda resources, resources_deps: {r: resources.get(r) for r in resources_deps},
                    context_creation_data.system_storage_def.required_resource_keys,
                ),
            )
        )
    )

    system_storage_data.run_storage.write_dagster_run_meta(
        DagsterRunMeta(
            run_id=run_config.run_id, timestamp=time.time(), pipeline_name=pipeline_def.name
        )
    )
    return system_storage_data


def construct_pipeline_execution_context(
    context_creation_data, scoped_resources_builder, system_storage_data, log_manager
):
    check.inst_param(context_creation_data, 'context_creation_data', ContextCreationData)
    scoped_resources_builder = check.inst_param(
        scoped_resources_builder if scoped_resources_builder else ScopedResourcesBuilder(),
        'scoped_resources_builder',
        ScopedResourcesBuilder,
    )
    check.inst_param(system_storage_data, 'system_storage_data', SystemStorageData)
    check.inst_param(log_manager, 'log_manager', DagsterLogManager)

    return SystemPipelineExecutionContext(
        SystemPipelineExecutionContextData(
            pipeline_def=context_creation_data.pipeline_def,
            mode_def=context_creation_data.mode_def,
            system_storage_def=context_creation_data.system_storage_def,
            run_config=context_creation_data.run_config,
            scoped_resources_builder=scoped_resources_builder,
            environment_config=context_creation_data.environment_config,
            run_storage=system_storage_data.run_storage,
            intermediates_manager=system_storage_data.intermediates_manager,
            file_manager=system_storage_data.file_manager,
            execution_target_handle=context_creation_data.execution_target_handle,
        ),
        log_manager=log_manager,
    )


class ResourcesStack(object):
    # Wraps an ExitStack to support execution in environments like Dagstermill, where we can't
    # wrap solid execution/the pipeline execution context lifecycle in an ordinary Python context
    # manager (because notebook execution is cell-by-cell in the Jupyter kernel, a subprocess we
    # don't directly control). In these environments we need to manually create and teardown
    # resources.
    def __init__(self, pipeline_def, environment_config, run_config, log_manager):
        check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
        check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
        check.inst_param(run_config, 'run_config', RunConfig)
        check.inst_param(log_manager, 'log_manager', DagsterLogManager)

        self.resource_instances = {}
        self.mode_definition = pipeline_def.get_mode_definition(run_config.mode)
        self.pipeline_def = pipeline_def
        self.environment_config = environment_config
        self.run_config = run_config
        self.log_manager = log_manager
        self.stack = ExitStack()

    def create(self):
        for resource_name, resource_def in sorted(self.mode_definition.resource_defs.items()):
            user_fn = create_resource_fn_lambda(
                self.pipeline_def,
                resource_def,
                self.environment_config.resources.get(resource_name, {}).get('config'),
                self.run_config.run_id,
                self.log_manager,
            )

            def _create_msg_fn(rn):
                return lambda: 'Error executing resource_fn on ResourceDefinition {name}'.format(
                    name=rn
                )

            resource_obj = self.stack.enter_context(
                user_code_context_manager(
                    user_fn, DagsterResourceFunctionError, _create_msg_fn(resource_name)
                )
            )

            self.resource_instances[resource_name] = resource_obj
        return ScopedResourcesBuilder(self.resource_instances)

    def teardown(self):
        self.stack.close()


def create_resource_fn_lambda(pipeline_def, resource_def, resource_config, run_id, log_manager):
    return lambda: resource_def.resource_fn(
        InitResourceContext(
            pipeline_def=pipeline_def,
            resource_def=resource_def,
            resource_config=resource_config,
            run_id=run_id,
            log_manager=log_manager,
        )
    )


def create_log_manager(context_creation_data):
    check.inst_param(context_creation_data, 'context_creation_data', ContextCreationData)

    pipeline_def, mode_def, environment_config, run_config = (
        context_creation_data.pipeline_def,
        context_creation_data.mode_def,
        context_creation_data.environment_config,
        context_creation_data.run_config,
    )

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

    return DagsterLogManager(
        run_id=run_config.run_id,
        logging_tags=get_logging_tags(
            context_creation_data.run_config, context_creation_data.pipeline_def
        ),
        loggers=loggers,
    )


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
def user_code_context_manager(user_fn, error_cls, msg_fn):
    '''Wraps the output of a user provided function that may yield or return a value and
    returns a generator that asserts it only yields a single value.
    '''
    check.callable_param(user_fn, 'user_fn')
    check.subclass_param(error_cls, 'error_cls', DagsterUserCodeExecutionError)

    with user_code_error_boundary(error_cls, msg_fn):
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
