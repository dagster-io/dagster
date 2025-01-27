import inspect
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Optional, cast

import dagster._check as check
from dagster._config import Shape
from dagster._core.definitions.configurable import ConfigurableDefinition
from dagster._core.definitions.resource_requirement import ensure_requirements_satisfied
from dagster._core.errors import DagsterInvalidConfigError, DagsterInvalidInvocationError

if TYPE_CHECKING:
    from dagster._core.definitions.resource_definition import ResourceDefinition
    from dagster._core.execution.context.init import InitResourceContext, UnboundInitResourceContext


def resource_invocation_result(
    resource_def: "ResourceDefinition", init_context: Optional["UnboundInitResourceContext"]
) -> Any:
    from dagster._core.definitions.resource_definition import (
        ResourceDefinition,
        has_at_least_one_parameter,
    )
    from dagster._core.execution.context.init import UnboundInitResourceContext

    check.inst_param(resource_def, "resource_def", ResourceDefinition)
    check.opt_inst_param(init_context, "init_context", UnboundInitResourceContext)

    if not resource_def.resource_fn:
        return None
    _init_context = _check_invocation_requirements(resource_def, init_context)

    resource_fn = resource_def.resource_fn
    val_or_gen = (
        resource_fn(_init_context) if has_at_least_one_parameter(resource_fn) else resource_fn()  # type: ignore  # (strict type guard)
    )
    if inspect.isgenerator(val_or_gen):

        @contextmanager
        def _wrap_gen():
            try:
                val = next(val_or_gen)
                yield val
            except StopIteration:
                check.failed("Resource generator must yield one item.")

        return _wrap_gen()
    else:
        return val_or_gen


def _check_invocation_requirements(
    resource_def: "ResourceDefinition", init_context: Optional["UnboundInitResourceContext"]
) -> "InitResourceContext":
    from dagster._core.definitions.resource_definition import has_at_least_one_parameter
    from dagster._core.execution.context.init import (
        InitResourceContext,
        build_init_resource_context,
    )

    context_provided = has_at_least_one_parameter(resource_def.resource_fn)
    if context_provided and resource_def.required_resource_keys and init_context is None:
        raise DagsterInvalidInvocationError(
            "Resource has required resources, but no context was provided. Use the "
            "`build_init_resource_context` function to construct a context with the required "
            "resources."
        )

    if context_provided and init_context is not None and resource_def.required_resource_keys:
        ensure_requirements_satisfied(
            init_context._resource_defs,  # noqa: SLF001
            list(resource_def.get_resource_requirements(source_key=None)),
        )

    # Check config requirements
    if not init_context and resource_def.config_schema.as_field().is_required:
        raise DagsterInvalidInvocationError(
            "Resource has required config schema, but no context was provided. "
            "Use the `build_init_resource_context` function to create a context with config."
        )

    resource_config = resolve_bound_config(
        init_context.resource_config if init_context else None, resource_def
    )

    # Construct a context if None was provided. This will initialize an ephemeral instance, and
    # console log manager.
    _init_context = init_context or build_init_resource_context()

    return InitResourceContext(
        resource_config=resource_config,
        resources=_init_context.resources,
        resource_def=resource_def,
        all_resource_defs={},
        instance=_init_context.instance,
        log_manager=_init_context.log,
    )


def _get_friendly_string(configurable_def: ConfigurableDefinition) -> str:
    from dagster._core.definitions.logger_definition import LoggerDefinition
    from dagster._core.definitions.node_definition import NodeDefinition
    from dagster._core.definitions.resource_definition import ResourceDefinition

    if isinstance(configurable_def, ResourceDefinition):
        return "resource"
    elif isinstance(configurable_def, LoggerDefinition):
        return "logger"
    elif isinstance(configurable_def, NodeDefinition):
        return configurable_def.node_type_str

    check.failed(f"Invalid definition type {configurable_def}")


def resolve_bound_config(config: Any, configurable_def: ConfigurableDefinition) -> Any:
    from dagster._config import process_config

    outer_config_shape = Shape({"config": configurable_def.get_config_field()})
    config_evr = process_config(outer_config_shape, {"config": config} if config else {})
    if not config_evr.success:
        raise DagsterInvalidConfigError(
            f"Error in config for {_get_friendly_string(configurable_def)}",
            config_evr.errors,
            config,
        )
    validated_config = cast(dict[str, Any], config_evr.value).get("config")
    mapped_config_evr = configurable_def.apply_config_mapping({"config": validated_config})
    if not mapped_config_evr.success:
        raise DagsterInvalidConfigError(
            f"Error when applying config mapping for {_get_friendly_string(configurable_def)}",
            mapped_config_evr.errors,
            validated_config,
        )
    validated_config = cast(dict[str, Any], mapped_config_evr.value).get("config")
    return validated_config
