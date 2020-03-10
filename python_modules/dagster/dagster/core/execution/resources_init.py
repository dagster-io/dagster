from collections import deque

from dagster import check
from dagster.core.definitions.resource import ScopedResourcesBuilder
from dagster.core.errors import (
    DagsterResourceFunctionError,
    DagsterUserCodeExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import DagsterEvent
from dagster.core.execution.plan.objects import StepInputSourceType
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.utils import EventGenerationManager, ensure_gen, merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.timing import format_duration, time_execution_scope

from .context.init import InitResourceContext


def resource_initialization_manager(
    execution_plan, environment_config, pipeline_run, log_manager, resource_keys_to_init,
):
    generator = resource_initialization_event_generator(
        execution_plan, environment_config, pipeline_run, log_manager, resource_keys_to_init,
    )
    return EventGenerationManager(generator, ScopedResourcesBuilder)


def resource_initialization_event_generator(
    execution_plan, environment_config, pipeline_run, log_manager, resource_keys_to_init
):
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
    check.inst_param(log_manager, 'log_manager', DagsterLogManager)
    check.set_param(resource_keys_to_init, 'resource_keys_to_init', of_type=str)

    if execution_plan.step_key_for_single_step_plans():
        step = execution_plan.get_step_by_key(execution_plan.step_key_for_single_step_plans())
        resource_log_manager = DagsterLogManager(
            pipeline_run.run_id,
            merge_dicts(log_manager.logging_tags, step.logging_tags),
            log_manager.loggers,
        )
    else:
        resource_log_manager = log_manager

    resource_instances = {}
    pipeline_def = execution_plan.pipeline_def
    mode_definition = pipeline_def.get_mode_definition(pipeline_run.mode)
    resource_managers = deque()
    generator_closed = False
    resource_init_times = {}

    try:
        if resource_keys_to_init:
            yield DagsterEvent.resource_init_start(
                execution_plan, resource_log_manager, resource_keys_to_init,
            )

        for resource_name, resource_def in sorted(mode_definition.resource_defs.items()):
            if not resource_name in resource_keys_to_init:
                continue
            resource_context = InitResourceContext(
                pipeline_def=pipeline_def,
                resource_def=resource_def,
                resource_config=environment_config.resources.get(resource_name, {}).get('config'),
                run_id=pipeline_run.run_id,
                log_manager=resource_log_manager,
            )
            manager = single_resource_generation_manager(
                resource_context, resource_name, resource_def
            )
            for event in manager.generate_setup_events():
                if event:
                    yield event
            initialized_resource = check.inst(manager.get_object(), InitializedResource)
            resource_instances[resource_name] = initialized_resource.resource
            resource_init_times[resource_name] = initialized_resource.duration
            resource_managers.append(manager)

        if resource_keys_to_init:
            yield DagsterEvent.resource_init_success(
                execution_plan, resource_log_manager, resource_instances, resource_init_times
            )
        yield ScopedResourcesBuilder(resource_instances)
    except GeneratorExit:
        # Shouldn't happen, but avoid runtime-exception in case this generator gets GC-ed
        # (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/).
        generator_closed = True
        raise
    except DagsterUserCodeExecutionError as dagster_user_error:
        yield DagsterEvent.resource_init_failure(
            execution_plan,
            resource_log_manager,
            resource_keys_to_init,
            serializable_error_info_from_exc_info(dagster_user_error.original_exc_info),
        )
        raise dagster_user_error
    finally:
        if not generator_closed:
            error = None
            while len(resource_managers) > 0:
                manager = resource_managers.pop()
                try:
                    for event in manager.generate_teardown_events():
                        yield event
                except DagsterUserCodeExecutionError as dagster_user_error:
                    error = dagster_user_error
            if error:
                yield DagsterEvent.resource_teardown_failure(
                    execution_plan,
                    resource_log_manager,
                    resource_keys_to_init,
                    serializable_error_info_from_exc_info(error.original_exc_info),
                )


class InitializedResource(object):
    ''' Utility class to wrap the untyped resource object emitted from the user-supplied
    resource function.  Used for distinguishing from the framework-yielded events in an
    `EventGenerationManager`-wrapped event stream.
    '''

    def __init__(self, obj, duration):
        self.resource = obj
        self.duration = duration


def single_resource_generation_manager(context, resource_name, resource_def):
    generator = single_resource_event_generator(context, resource_name, resource_def)
    return EventGenerationManager(generator, InitializedResource)


def single_resource_event_generator(context, resource_name, resource_def):
    try:
        msg_fn = lambda: 'Error executing resource_fn on ResourceDefinition {name}'.format(
            name=resource_name
        )
        with user_code_error_boundary(DagsterResourceFunctionError, msg_fn):
            try:
                with time_execution_scope() as timer_result:
                    resource_or_gen = resource_def.resource_fn(context)
                    gen = ensure_gen(resource_or_gen)
                    resource = next(gen)
                yield InitializedResource(resource, format_duration(timer_result.millis))
            except StopIteration:
                check.failed(
                    'Resource generator {name} must yield one item.'.format(name=resource_name)
                )
    except DagsterUserCodeExecutionError as dagster_user_error:
        raise dagster_user_error

    with user_code_error_boundary(DagsterResourceFunctionError, msg_fn):
        try:
            next(gen)
        except StopIteration:
            pass
        else:
            check.failed(
                'Resource generator {name} yielded more than one item.'.format(name=resource_name)
            )


def get_required_resource_keys_to_init(execution_plan, system_storage_def):
    resource_keys = set()

    resource_keys = resource_keys.union(system_storage_def.required_resource_keys)

    for step_key, step in execution_plan.step_dict.items():
        if step_key not in execution_plan.step_keys_to_execute:
            continue
        resource_keys = resource_keys.union(
            get_required_resource_keys_for_step(
                step, execution_plan.pipeline_def, system_storage_def
            )
        )

    return frozenset(resource_keys)


def get_required_resource_keys_for_step(execution_step, pipeline_def, system_storage_def):
    resource_keys = set()

    # add all the system storage resource keys
    resource_keys = resource_keys.union(system_storage_def.required_resource_keys)
    solid_def = pipeline_def.get_solid(execution_step.solid_handle).definition

    # add all the solid compute resource keys
    resource_keys = resource_keys.union(solid_def.required_resource_keys)

    # add input type and input hydration config resource keys
    for step_input in execution_step.step_inputs:
        resource_keys = resource_keys.union(step_input.dagster_type.required_resource_keys)
        if (
            step_input.source_type == StepInputSourceType.CONFIG
            and step_input.dagster_type.input_hydration_config
        ):
            resource_keys = resource_keys.union(
                step_input.dagster_type.input_hydration_config.required_resource_keys()
            )

    # add output type and output materialization config resource keys
    for step_output in execution_step.step_outputs:
        resource_keys = resource_keys.union(step_output.dagster_type.required_resource_keys)
        if (
            step_output.should_materialize
            and step_output.dagster_type.output_materialization_config
        ):
            resource_keys = resource_keys.union(
                step_output.dagster_type.output_materialization_config.required_resource_keys()
            )

    # add all the storage-compatible plugin resource keys
    for dagster_type in solid_def.all_dagster_types():
        for auto_plugin in dagster_type.auto_plugins:
            if auto_plugin.compatible_with_storage_def(system_storage_def):
                resource_keys = resource_keys.union(auto_plugin.required_resource_keys())

    return frozenset(resource_keys)
