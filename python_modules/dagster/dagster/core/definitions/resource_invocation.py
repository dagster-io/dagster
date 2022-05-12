import inspect
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict, Optional, cast

import dagster._check as check
from dagster.core.errors import DagsterInvalidConfigError, DagsterInvalidInvocationError

from ...config import Shape
from ..decorator_utils import get_function_params

if TYPE_CHECKING:
    from dagster.core.definitions.resource_definition import ResourceDefinition
    from dagster.core.execution.context.init import InitResourceContext, UnboundInitResourceContext


def resource_invocation_result(
    resource_def: "ResourceDefinition", init_context: Optional["InitResourceContext"]
) -> Any:
    from .resource_definition import is_context_provided

    if not resource_def.resource_fn:
        return None
    init_context = _check_invocation_requirements(resource_def, init_context)

    val_or_gen = (
        resource_def.resource_fn(init_context)
        if is_context_provided(get_function_params(resource_def.resource_fn))
        else resource_def.resource_fn()
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
    resource_def: "ResourceDefinition", init_context: Optional["InitResourceContext"]
) -> "InitResourceContext":
    from dagster.core.execution.context.init import InitResourceContext, build_init_resource_context

    if resource_def.required_resource_keys and init_context is None:
        raise DagsterInvalidInvocationError(
            "Resource has required resources, but no context was provided. Use the "
            "`build_init_resource_context` function to construct a context with the required "
            "resources."
        )

    if init_context is not None and resource_def.required_resource_keys:
        resources_dict = cast(
            "InitResourceContext",
            init_context,
        ).resources._asdict()  # type: ignore[attr-defined]

        for resource_key in resource_def.required_resource_keys:
            if resource_key not in resources_dict:
                raise DagsterInvalidInvocationError(
                    f'Resource requires resource "{resource_key}", but no resource '
                    "with that key was found on the context."
                )

    # Check config requirements
    if not init_context and resource_def.config_schema.as_field().is_required:
        raise DagsterInvalidInvocationError(
            "Resource has required config schema, but no context was provided. "
            "Use the `build_init_resource_context` function to create a context with config."
        )

    resource_config = _resolve_bound_config(
        init_context.resource_config if init_context else None, resource_def
    )

    # Construct a context if None was provided. This will initialize an ephemeral instance, and
    # console log manager.
    init_context = init_context or build_init_resource_context()

    return InitResourceContext(
        resource_config=resource_config,
        resources=init_context.resources,
        resource_def=resource_def,
        instance=init_context.instance,
        log_manager=init_context.log,
    )


def _resolve_bound_config(resource_config: Any, resource_def: "ResourceDefinition") -> Any:
    from dagster.config.validate import process_config

    outer_config_shape = Shape({"config": resource_def.get_config_field()})
    config_evr = process_config(
        outer_config_shape, {"config": resource_config} if resource_config else {}
    )
    if not config_evr.success:
        raise DagsterInvalidConfigError(
            "Error in config for resource ", config_evr.errors, resource_config
        )
    validated_config = cast(Dict[str, Any], config_evr.value).get("config")
    mapped_config_evr = resource_def.apply_config_mapping({"config": validated_config})
    if not mapped_config_evr.success:
        raise DagsterInvalidConfigError(
            "Error when applying config mapping for resource ",
            mapped_config_evr.errors,
            validated_config,
        )
    validated_config = cast(Dict[str, Any], mapped_config_evr.value).get("config")
    return validated_config
