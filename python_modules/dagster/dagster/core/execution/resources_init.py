from collections import deque
from typing import AbstractSet, Deque, Dict, Optional, cast

from dagster import check
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.definitions.resource import ResourceDefinition, ScopedResourcesBuilder
from dagster.core.errors import (
    DagsterInvariantViolationError,
    DagsterResourceFunctionError,
    DagsterUserCodeExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import DagsterEvent
from dagster.core.execution.plan.inputs import (
    StepInput,
    UnresolvedCollectStepInput,
    UnresolvedMappedStepInput,
)
from dagster.core.execution.plan.plan import ExecutionPlan, StepHandleUnion
from dagster.core.execution.plan.step import ExecutionStep
from dagster.core.instance import DagsterInstance
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.system_config.objects import ResourceConfig
from dagster.core.utils import toposort
from dagster.utils import EventGenerationManager, ensure_gen
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.timing import format_duration, time_execution_scope

from .context.init import InitResourceContext


def resource_initialization_manager(
    resource_defs: Dict[str, ResourceDefinition],
    resource_configs: Dict[str, ResourceConfig],
    log_manager: DagsterLogManager,
    execution_plan: Optional[ExecutionPlan],
    pipeline_run: Optional[PipelineRun],
    resource_keys_to_init: Optional[AbstractSet[str]],
    instance: Optional[DagsterInstance],
    emit_persistent_events: Optional[bool],
    pipeline_def_for_backwards_compat: Optional[PipelineDefinition],
):
    generator = resource_initialization_event_generator(
        resource_defs=resource_defs,
        resource_configs=resource_configs,
        log_manager=log_manager,
        execution_plan=execution_plan,
        pipeline_run=pipeline_run,
        resource_keys_to_init=resource_keys_to_init,
        instance=instance,
        emit_persistent_events=emit_persistent_events,
        pipeline_def_for_backwards_compat=pipeline_def_for_backwards_compat,
    )
    return EventGenerationManager(generator, ScopedResourcesBuilder)


def _resolve_resource_dependencies(resource_defs):
    """Generates a dictionary that maps resource key to resource keys it requires for initialization"""
    resource_dependencies = {
        key: resource_def.required_resource_keys for key, resource_def in resource_defs.items()
    }
    return resource_dependencies


def _get_dependencies(resource_name, resource_deps):
    """Get all resources that must be initialized before resource_name can be initialized.

    Uses dfs to get all required dependencies from a particular resource. If dependencies are
        cyclic, raise a DagsterInvariantViolationError.
    """
    path = set()  # resources we are currently checking the dependencies of
    reqd_resources = set()

    # adds dependencies for a given resource key to reqd_resources
    def _get_deps_helper(resource_key):
        path.add(resource_key)
        for reqd_resource_key in resource_deps[resource_key]:
            if reqd_resource_key in path:
                raise DagsterInvariantViolationError(
                    'Resource key "{key}" transitively depends on itself.'.format(
                        key=reqd_resource_key
                    )
                )
            _get_deps_helper(reqd_resource_key)
        path.remove(resource_key)
        reqd_resources.add(resource_key)

    _get_deps_helper(resource_name)
    return set(reqd_resources)


def _core_resource_initialization_event_generator(
    resource_defs: Dict[str, ResourceDefinition],
    resource_configs: Dict[str, ResourceConfig],
    resource_log_manager: DagsterLogManager,
    resource_managers: Deque[EventGenerationManager],
    execution_plan: Optional[ExecutionPlan],
    pipeline_run: Optional[PipelineRun],
    resource_keys_to_init: Optional[AbstractSet[str]],
    instance: Optional[DagsterInstance],
    emit_persistent_events: Optional[bool],
    pipeline_def_for_backwards_compat: Optional[PipelineDefinition],
):

    pipeline_name = None
    if emit_persistent_events:
        check.invariant(
            pipeline_run and execution_plan,
            "If emit_persistent_events is enabled, then pipeline_run and execution_plan must be provided",
        )
        pipeline_name = cast(PipelineRun, pipeline_run).pipeline_name
    resource_keys_to_init = check.opt_set_param(resource_keys_to_init, "resource_keys_to_init")
    resource_instances: Dict[str, "InitializedResource"] = {}
    resource_init_times = {}
    try:
        if emit_persistent_events and resource_keys_to_init:
            yield DagsterEvent.resource_init_start(
                pipeline_name,
                execution_plan,
                resource_log_manager,
                resource_keys_to_init,
            )

        resource_dependencies = _resolve_resource_dependencies(resource_defs)

        for level in toposort(resource_dependencies):
            for resource_name in level:
                resource_def = resource_defs[resource_name]
                if not resource_name in resource_keys_to_init:
                    continue

                resource_context = InitResourceContext(
                    resource_def=resource_def,
                    resource_config=resource_configs[resource_name].config,
                    pipeline_run=pipeline_run,
                    # Add tags with information about the resource
                    log_manager=resource_log_manager.with_tags(
                        resource_name=resource_name,
                        resource_fn_name=str(resource_def.resource_fn.__name__),
                    ),
                    resource_instance_dict=resource_instances,
                    required_resource_keys=resource_def.required_resource_keys,
                    instance=instance,
                    pipeline_def_for_backwards_compat=pipeline_def_for_backwards_compat,
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

        if emit_persistent_events and resource_keys_to_init:
            yield DagsterEvent.resource_init_success(
                pipeline_name,
                execution_plan,
                resource_log_manager,
                resource_instances,
                resource_init_times,
            )
        yield ScopedResourcesBuilder(resource_instances)
    except DagsterUserCodeExecutionError as dagster_user_error:
        # Can only end up in this state if we attempt to initialize a resource, so
        # resource_keys_to_init cannot be empty
        if emit_persistent_events:
            yield DagsterEvent.resource_init_failure(
                pipeline_name,
                execution_plan,
                resource_log_manager,
                resource_keys_to_init,
                serializable_error_info_from_exc_info(dagster_user_error.original_exc_info),
            )
        raise dagster_user_error


def resource_initialization_event_generator(
    resource_defs: Dict[str, ResourceDefinition],
    resource_configs: Dict[str, ResourceConfig],
    log_manager: DagsterLogManager,
    execution_plan: Optional[ExecutionPlan],
    pipeline_run: Optional[PipelineRun],
    resource_keys_to_init: Optional[AbstractSet[str]],
    instance: Optional[DagsterInstance],
    emit_persistent_events: Optional[bool],
    pipeline_def_for_backwards_compat: Optional[PipelineDefinition],
):
    check.inst_param(log_manager, "log_manager", DagsterLogManager)
    resource_keys_to_init = check.opt_set_param(
        resource_keys_to_init, "resource_keys_to_init", of_type=str
    )
    check.opt_inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.opt_inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.opt_inst_param(instance, "instance", DagsterInstance)

    if execution_plan and execution_plan.step_handle_for_single_step_plans():
        step = execution_plan.get_step(
            cast(
                StepHandleUnion,
                cast(ExecutionPlan, execution_plan).step_handle_for_single_step_plans(),
            )
        )
        resource_log_manager = log_manager.with_tags(**cast(ExecutionStep, step).logging_tags)
    else:
        resource_log_manager = log_manager

    generator_closed = False
    resource_managers: Deque[EventGenerationManager] = deque()

    try:

        yield from _core_resource_initialization_event_generator(
            resource_defs=resource_defs,
            resource_configs=resource_configs,
            resource_log_manager=resource_log_manager,
            resource_managers=resource_managers,
            execution_plan=execution_plan,
            pipeline_run=pipeline_run,
            resource_keys_to_init=resource_keys_to_init,
            instance=instance,
            emit_persistent_events=emit_persistent_events,
            pipeline_def_for_backwards_compat=pipeline_def_for_backwards_compat,
        )
    except GeneratorExit:
        # Shouldn't happen, but avoid runtime-exception in case this generator gets GC-ed
        # (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/).
        generator_closed = True
        raise
    finally:
        if not generator_closed:
            error = None
            while len(resource_managers) > 0:
                manager = resource_managers.pop()
                try:
                    yield from manager.generate_teardown_events()
                except DagsterUserCodeExecutionError as dagster_user_error:
                    error = dagster_user_error
            if error and emit_persistent_events:
                yield DagsterEvent.resource_teardown_failure(
                    cast(PipelineRun, pipeline_run).pipeline_name,
                    execution_plan,
                    resource_log_manager,
                    resource_keys_to_init,
                    serializable_error_info_from_exc_info(error.original_exc_info),
                )


class InitializedResource:
    """Utility class to wrap the untyped resource object emitted from the user-supplied
    resource function.  Used for distinguishing from the framework-yielded events in an
    `EventGenerationManager`-wrapped event stream.
    """

    def __init__(self, obj, duration):
        self.resource = obj
        self.duration = duration


def single_resource_generation_manager(context, resource_name, resource_def):
    generator = single_resource_event_generator(context, resource_name, resource_def)
    return EventGenerationManager(generator, InitializedResource)


def single_resource_event_generator(context, resource_name, resource_def):
    try:
        msg_fn = lambda: "Error executing resource_fn on ResourceDefinition {name}".format(
            name=resource_name
        )
        with user_code_error_boundary(DagsterResourceFunctionError, msg_fn):
            try:
                with time_execution_scope() as timer_result:
                    resource_or_gen = resource_def.resource_fn(context)
                    gen = ensure_gen(resource_or_gen)
                    resource = next(gen)
                resource = InitializedResource(resource, format_duration(timer_result.millis))
            except StopIteration:
                check.failed(
                    "Resource generator {name} must yield one item.".format(name=resource_name)
                )

        yield resource

    except DagsterUserCodeExecutionError as dagster_user_error:
        raise dagster_user_error

    with user_code_error_boundary(DagsterResourceFunctionError, msg_fn):
        try:
            next(gen)
        except StopIteration:
            pass
        else:
            check.failed(
                "Resource generator {name} yielded more than one item.".format(name=resource_name)
            )


def get_required_resource_keys_to_init(
    execution_plan, pipeline_def, environment_config, intermediate_storage_def
):
    resource_keys = set()

    if intermediate_storage_def is not None:
        resource_keys = resource_keys.union(intermediate_storage_def.required_resource_keys)

    for step_handle, step in execution_plan.step_dict.items():
        if step_handle not in execution_plan.step_handles_to_execute:
            continue

        hook_defs = pipeline_def.get_all_hooks_for_handle(step.solid_handle)
        for hook_def in hook_defs:
            resource_keys = resource_keys.union(hook_def.required_resource_keys)

        resource_keys = resource_keys.union(
            get_required_resource_keys_for_step(
                pipeline_def, step, execution_plan, environment_config, intermediate_storage_def
            )
        )

    return frozenset(resource_keys)


def get_required_resource_keys_for_step(
    pipeline_def, execution_step, execution_plan, environment_config, intermediate_storage_def
):
    resource_keys = set()

    mode_definition = pipeline_def.get_mode_definition(environment_config.mode)

    resource_dependencies = _resolve_resource_dependencies(mode_definition.resource_defs)

    # add all the intermediate storage resource keys
    if intermediate_storage_def is not None:
        resource_keys = resource_keys.union(intermediate_storage_def.required_resource_keys)

    # add all the solid compute resource keys
    solid_def = pipeline_def.get_solid(execution_step.solid_handle).definition
    resource_keys = resource_keys.union(solid_def.required_resource_keys)

    # add input type, input loader, and input io manager resource keys
    for step_input in execution_step.step_inputs:
        input_def = step_input.source.get_input_def(pipeline_def)

        resource_keys = resource_keys.union(input_def.dagster_type.required_resource_keys)

        resource_keys = resource_keys.union(step_input.source.required_resource_keys(pipeline_def))

        if isinstance(step_input, StepInput):
            source_handles = step_input.get_step_output_handle_dependencies()
        elif isinstance(step_input, (UnresolvedMappedStepInput, UnresolvedCollectStepInput)):
            # Placeholder handles will allow lookup of the unresolved execution steps
            # for what resources will be needed once the steps resolve
            source_handles = step_input.get_step_output_handle_deps_with_placeholders()
        else:
            check.failed(f"Unexpected step input type {step_input}")

        for source_handle in source_handles:
            source_manager_key = execution_plan.get_manager_key(source_handle, pipeline_def)
            if source_manager_key:
                resource_keys = resource_keys.union([source_manager_key])

    # add output type, output materializer, and output io manager resource keys
    for step_output in execution_step.step_outputs:

        # Load the output type
        output_def = solid_def.output_def_named(step_output.name)

        resource_keys = resource_keys.union(output_def.dagster_type.required_resource_keys)
        if step_output.should_materialize and output_def.dagster_type.materializer:
            resource_keys = resource_keys.union(
                output_def.dagster_type.materializer.required_resource_keys()
            )
        if output_def.io_manager_key:
            resource_keys = resource_keys.union([output_def.io_manager_key])

    # add all the storage-compatible plugin resource keys
    for dagster_type in solid_def.all_dagster_types():
        for auto_plugin in dagster_type.auto_plugins:
            if intermediate_storage_def is not None:
                if auto_plugin.compatible_with_storage_def(intermediate_storage_def):
                    resource_keys = resource_keys.union(auto_plugin.required_resource_keys())

    for resource_name in resource_keys:
        resource_keys = resource_keys.union(
            set(_get_dependencies(resource_name, resource_dependencies))
        )
    return frozenset(resource_keys)
