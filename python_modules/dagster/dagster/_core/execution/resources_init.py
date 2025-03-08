import inspect
from asyncio import AbstractEventLoop
from collections import deque
from collections.abc import Generator, Mapping
from contextlib import ContextDecorator
from typing import AbstractSet, Any, Callable, Optional, Union, cast  # noqa: UP035

import dagster._check as check
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.resource_definition import (
    ResourceDefinition,
    ScopedResourcesBuilder,
    has_at_least_one_parameter,
)
from dagster._core.errors import (
    DagsterInvariantViolationError,
    DagsterResourceFunctionError,
    DagsterUserCodeExecutionError,
    user_code_error_boundary,
)
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.init import InitResourceContext
from dagster._core.execution.plan.inputs import (
    StepInput,
    UnresolvedCollectStepInput,
    UnresolvedMappedStepInput,
)
from dagster._core.execution.plan.plan import ExecutionPlan, StepHandleUnion
from dagster._core.execution.plan.step import ExecutionStep, IExecutionStep
from dagster._core.instance import DagsterInstance
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.system_config.objects import ResourceConfig
from dagster._core.utils import toposort
from dagster._utils import EventGenerationManager, ensure_gen
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.timing import format_duration, time_execution_scope


def resource_initialization_manager(
    resource_defs: Mapping[str, ResourceDefinition],
    resource_configs: Mapping[str, ResourceConfig],
    log_manager: DagsterLogManager,
    execution_plan: Optional[ExecutionPlan],
    dagster_run: Optional[DagsterRun],
    resource_keys_to_init: Optional[AbstractSet[str]],
    instance: Optional[DagsterInstance],
    emit_persistent_events: Optional[bool],
    event_loop: Optional[AbstractEventLoop],
):
    generator = resource_initialization_event_generator(
        resource_defs=resource_defs,
        resource_configs=resource_configs,
        log_manager=log_manager,
        execution_plan=execution_plan,
        dagster_run=dagster_run,
        resource_keys_to_init=resource_keys_to_init,
        instance=instance,
        emit_persistent_events=emit_persistent_events,
        event_loop=event_loop,
    )
    return EventGenerationManager(generator, ScopedResourcesBuilder)


def resolve_resource_dependencies(
    resource_defs: Mapping[str, ResourceDefinition],
) -> Mapping[str, AbstractSet[str]]:
    """Generates a dictionary that maps resource key to resource keys it requires for initialization."""
    resource_dependencies = {
        key: resource_def.get_required_resource_keys(resource_defs)
        for key, resource_def in resource_defs.items()
    }
    return resource_dependencies


def ensure_resource_deps_satisfiable(resource_deps: Mapping[str, AbstractSet[str]]) -> None:
    path = set()  # resources we are currently checking the dependencies of

    def _helper(resource_key):
        path.add(resource_key)
        for reqd_resource_key in resource_deps[resource_key]:
            if reqd_resource_key in path:
                raise DagsterInvariantViolationError(
                    f'Resource key "{reqd_resource_key}" transitively depends on itself.'
                )
            if reqd_resource_key not in resource_deps:
                raise DagsterInvariantViolationError(
                    f"Resource with key '{reqd_resource_key}' required by resource with key"
                    f" '{resource_key}', but not provided."
                )
            _helper(reqd_resource_key)
        path.remove(resource_key)

    for resource_key in sorted(list(resource_deps.keys())):
        _helper(resource_key)


def get_dependencies(
    resource_name: str, resource_deps: Mapping[str, AbstractSet[str]]
) -> AbstractSet[str]:
    """Get all resources that must be initialized before resource_name can be initialized.

    Uses dfs to get all required dependencies from a particular resource. Assumes that resource dependencies are not cyclic (check performed by a different function).
    """
    reqd_resources = set()

    # adds dependencies for a given resource key to reqd_resources
    def _get_deps_helper(resource_key):
        for reqd_resource_key in resource_deps[resource_key]:
            _get_deps_helper(reqd_resource_key)
        reqd_resources.add(resource_key)

    _get_deps_helper(resource_name)
    return reqd_resources


def _core_resource_initialization_event_generator(
    resource_defs: Mapping[str, ResourceDefinition],
    resource_configs: Mapping[str, ResourceConfig],
    resource_log_manager: DagsterLogManager,
    resource_managers: deque[EventGenerationManager],
    execution_plan: Optional[ExecutionPlan],
    dagster_run: Optional[DagsterRun],
    resource_keys_to_init: Optional[AbstractSet[str]],
    instance: Optional[DagsterInstance],
    emit_persistent_events: Optional[bool],
    event_loop,
):
    job_name = ""  # Must be initialized to a string to satisfy typechecker
    contains_generator = False
    if emit_persistent_events:
        check.invariant(
            dagster_run and execution_plan,
            "If emit_persistent_events is enabled, then dagster_run and execution_plan must be"
            " provided",
        )
        job_name = cast(DagsterRun, dagster_run).job_name
    resource_keys_to_init = check.opt_set_param(resource_keys_to_init, "resource_keys_to_init")
    resource_instances: dict[str, InitializedResource] = {}
    resource_init_times = {}
    try:
        if emit_persistent_events and resource_keys_to_init:
            yield DagsterEvent.resource_init_start(
                job_name,
                cast(ExecutionPlan, execution_plan),
                resource_log_manager,
                resource_keys_to_init,
            )

        resource_dependencies = resolve_resource_dependencies(resource_defs)
        for level in toposort(resource_dependencies):
            for resource_name in level:
                resource_def = resource_defs[resource_name]
                if resource_name not in resource_keys_to_init:
                    continue

                resource_fn = cast(Callable[[InitResourceContext], Any], resource_def.resource_fn)
                resources = ScopedResourcesBuilder(resource_instances).build(
                    resource_def.get_required_resource_keys(resource_defs)
                )
                resource_context = InitResourceContext(
                    resource_def=resource_def,
                    resource_config=resource_configs[resource_name].config,
                    dagster_run=dagster_run,
                    # Add tags with information about the resource
                    log_manager=resource_log_manager.with_tags(
                        resource_name=resource_name,
                        resource_fn_name=str(resource_fn.__name__),
                    ),
                    resources=resources,
                    instance=instance,
                    all_resource_defs=resource_defs,
                    event_loop=event_loop,
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
                contains_generator = contains_generator or initialized_resource.is_generator
                resource_managers.append(manager)

        if emit_persistent_events and resource_keys_to_init:
            yield DagsterEvent.resource_init_success(
                job_name,
                cast(ExecutionPlan, execution_plan),
                resource_log_manager,
                resource_instances,
                resource_init_times,
            )

        delta_res_keys = resource_keys_to_init - set(resource_instances.keys())
        check.invariant(
            not delta_res_keys,
            f"resources instances do not align with resource to init, difference: {delta_res_keys}",
        )
        yield ScopedResourcesBuilder(resource_instances, contains_generator)
    except DagsterUserCodeExecutionError as dagster_user_error:
        # Can only end up in this state if we attempt to initialize a resource, so
        # resource_keys_to_init cannot be empty
        if emit_persistent_events:
            yield DagsterEvent.resource_init_failure(
                job_name,
                cast(ExecutionPlan, execution_plan),
                resource_log_manager,
                resource_keys_to_init,
                serializable_error_info_from_exc_info(dagster_user_error.original_exc_info),
            )
        raise dagster_user_error


def resource_initialization_event_generator(
    resource_defs: Mapping[str, ResourceDefinition],
    resource_configs: Mapping[str, ResourceConfig],
    log_manager: DagsterLogManager,
    execution_plan: Optional[ExecutionPlan],
    dagster_run: Optional[DagsterRun],
    resource_keys_to_init: Optional[AbstractSet[str]],
    instance: Optional[DagsterInstance],
    emit_persistent_events: Optional[bool],
    event_loop: Optional[AbstractEventLoop],
):
    check.inst_param(log_manager, "log_manager", DagsterLogManager)
    resource_keys_to_init = check.opt_set_param(
        resource_keys_to_init, "resource_keys_to_init", of_type=str
    )
    check.opt_inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.opt_inst_param(dagster_run, "dagster_run", DagsterRun)
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
    resource_managers: deque[EventGenerationManager] = deque()

    try:
        yield from _core_resource_initialization_event_generator(
            resource_defs=resource_defs,
            resource_configs=resource_configs,
            resource_log_manager=resource_log_manager,
            resource_managers=resource_managers,
            execution_plan=execution_plan,
            dagster_run=dagster_run,
            resource_keys_to_init=resource_keys_to_init,
            instance=instance,
            emit_persistent_events=emit_persistent_events,
            event_loop=event_loop,
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
                    cast(DagsterRun, dagster_run).job_name,
                    cast(ExecutionPlan, execution_plan),
                    resource_log_manager,
                    resource_keys_to_init,
                    serializable_error_info_from_exc_info(error.original_exc_info),
                )


class InitializedResource:
    """Utility class to wrap the untyped resource object emitted from the user-supplied
    resource function.  Used for distinguishing from the framework-yielded events in an
    `EventGenerationManager`-wrapped event stream.
    """

    def __init__(self, obj: Any, duration: str, is_generator: bool):
        self.resource = obj
        self.duration = duration
        self.is_generator = is_generator


def single_resource_generation_manager(
    context: InitResourceContext, resource_name: str, resource_def: ResourceDefinition
) -> EventGenerationManager:
    generator = single_resource_event_generator(context, resource_name, resource_def)
    # EventGenerationManager needs to be renamed/generalized so that it doesn't only take event generators
    return EventGenerationManager(generator, InitializedResource)


def single_resource_event_generator(
    context: InitResourceContext, resource_name: str, resource_def: ResourceDefinition
) -> Generator[InitializedResource, None, None]:
    try:
        msg_fn = lambda: f"Error executing resource_fn on ResourceDefinition {resource_name}"
        with user_code_error_boundary(
            DagsterResourceFunctionError, msg_fn, log_manager=context.log
        ):
            try:
                with time_execution_scope() as timer_result:
                    resource_or_gen = (
                        resource_def.resource_fn(context)
                        if has_at_least_one_parameter(resource_def.resource_fn)
                        else resource_def.resource_fn()  # type: ignore[call-arg]
                    )

                    # Flag for whether resource is generator. This is used to ensure that teardown
                    # occurs when resources are initialized out of execution.
                    is_gen = inspect.isgenerator(resource_or_gen) or isinstance(
                        resource_or_gen, ContextDecorator
                    )

                    resource_iter = _wrapped_resource_iterator(resource_or_gen)
                    resource = next(resource_iter)
                resource = InitializedResource(
                    resource, format_duration(timer_result.millis), is_gen
                )
            except StopIteration:
                check.failed(f"Resource generator {resource_name} must yield one item.")

        yield resource

    except DagsterUserCodeExecutionError as dagster_user_error:
        raise dagster_user_error

    with user_code_error_boundary(DagsterResourceFunctionError, msg_fn, log_manager=context.log):
        try:
            next(resource_iter)
        except StopIteration:
            pass
        else:
            check.failed(f"Resource generator {resource_name} yielded more than one item.")


def get_required_resource_keys_to_init(
    execution_plan: ExecutionPlan,
    job_def: JobDefinition,
) -> AbstractSet[str]:
    resource_keys: set[str] = set()

    for step_handle, step in execution_plan.step_dict.items():
        if step_handle not in execution_plan.step_handles_to_execute:
            continue

        hook_defs = job_def.get_all_hooks_for_handle(step.node_handle)
        for hook_def in hook_defs:
            resource_keys = resource_keys.union(hook_def.required_resource_keys)

        resource_keys = resource_keys.union(
            get_required_resource_keys_for_step(job_def, step, execution_plan)
        )

    return frozenset(get_transitive_required_resource_keys(resource_keys, job_def.resource_defs))


def get_transitive_required_resource_keys(
    required_resource_keys: AbstractSet[str], resource_defs: Mapping[str, ResourceDefinition]
) -> AbstractSet[str]:
    resource_dependencies = resolve_resource_dependencies(resource_defs)
    ensure_resource_deps_satisfiable(resource_dependencies)

    transitive_required_resource_keys: set[str] = set()

    for resource_key in required_resource_keys:
        transitive_required_resource_keys = transitive_required_resource_keys.union(
            set(get_dependencies(resource_key, resource_dependencies))
        )

    return transitive_required_resource_keys


def get_required_resource_keys_for_step(
    job_def: JobDefinition, execution_step: IExecutionStep, execution_plan: ExecutionPlan
) -> AbstractSet[str]:
    resource_keys: set[str] = set()

    # add all the op compute resource keys
    node_def = job_def.get_node(execution_step.node_handle).definition
    resource_keys = resource_keys.union(node_def.required_resource_keys)  # type: ignore  # (should be OpDefinition)

    # add input type, input loader, and input io manager resource keys
    for step_input in execution_step.step_inputs:
        input_def = node_def.input_def_named(step_input.name)

        resource_keys = resource_keys.union(input_def.dagster_type.required_resource_keys)

        resource_keys = resource_keys.union(
            step_input.source.required_resource_keys(
                job_def, execution_step.node_handle, step_input.name
            )
        )

        if input_def.input_manager_key:
            resource_keys = resource_keys.union([input_def.input_manager_key])

        if isinstance(step_input, StepInput):
            source_handles = step_input.get_step_output_handle_dependencies()
        elif isinstance(step_input, (UnresolvedMappedStepInput, UnresolvedCollectStepInput)):
            # Placeholder handles will allow lookup of the unresolved execution steps
            # for what resources will be needed once the steps resolve
            source_handles = step_input.get_step_output_handle_deps_with_placeholders()
        else:
            check.failed(f"Unexpected step input type {step_input}")

        for source_handle in source_handles:
            source_manager_key = execution_plan.get_manager_key(source_handle, job_def)
            if source_manager_key:
                resource_keys = resource_keys.union([source_manager_key])

    # add output type and output io manager resource keys
    for step_output in execution_step.step_outputs:
        # Load the output type
        output_def = node_def.output_def_named(step_output.name)

        resource_keys = resource_keys.union(output_def.dagster_type.required_resource_keys)
        if output_def.io_manager_key:
            resource_keys = resource_keys.union([output_def.io_manager_key])

    return frozenset(resource_keys)


def _wrapped_resource_iterator(
    resource_or_gen: Union[Any, Generator[Any, None, None]],
) -> Generator[Any, None, None]:
    """Returns an iterator which yields a single item, which is the resource.

    If the resource is not a context manager, then resource teardown happens following the first yield.
    If the resource is a context manager, then resource initialization happens as the passed-in
    context manager opens. Resource teardown happens as the passed-in context manager closes (which will occur after all compute is finished).
    """
    # Context managers created using contextlib.contextdecorator are not usable as iterators.
    # Opening context manager and directly yielding preserves initialization/teardown behavior,
    # while also letting the context manager be used as an iterator.
    if isinstance(resource_or_gen, ContextDecorator):

        def _gen_resource():
            with resource_or_gen as resource:  # pyright: ignore[reportGeneralTypeIssues]
                yield resource

        return _gen_resource()

    # Otherwise, coerce to generator without opening context manager
    return ensure_gen(resource_or_gen)
