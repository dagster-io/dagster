from collections.abc import Mapping
from typing import Any, Optional, cast

from dagster import Field, Permissive
from dagster._config.validate import process_config
from dagster._core.errors import DagsterInvalidConfigError

SHARED_CONTAINER_CONTEXT_SCHEMA = Permissive(
    {
        "env_vars": Field(
            [str],
            is_required=False,
            description=(
                "The list of environment variables names to include in the container. Each can be"
                " of the form KEY=VALUE or just KEY (in which case the value will be pulled from"
                " the local environment)"
            ),
        ),
    }
)


# Process fields shared by container contexts in all environments (docker / k8s / ecs etc.)
def process_shared_container_context_config(
    container_context_config: Optional[Mapping[str, Any]],
) -> Mapping[str, Any]:
    shared_container_context = process_config(
        SHARED_CONTAINER_CONTEXT_SCHEMA, container_context_config or {}
    )
    if not shared_container_context.success:
        raise DagsterInvalidConfigError(
            "Errors while parsing container context",
            shared_container_context.errors,
            container_context_config,
        )

    return cast("dict[str, Any]", shared_container_context.value)
