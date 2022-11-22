import re
from typing import Any, Mapping

from .tasks import DagsterEcsTaskDefinitionConfig


def sanitize_family(family):
    # Trim the location name and remove special characters
    return re.sub(r"[^\w^\-]", "", family)[:255]


def task_definitions_match(
    desired_task_definition_config: DagsterEcsTaskDefinitionConfig,
    existing_task_definition: Mapping[str, Any],
    container_name: str,
) -> bool:
    if not any(
        [
            container["name"] == container_name
            for container in existing_task_definition["containerDefinitions"]
        ]
    ):
        return False

    existing_task_definition_config = DagsterEcsTaskDefinitionConfig.from_task_definition_dict(
        existing_task_definition, container_name
    )

    # sidecars are checked separately below
    match_without_sidecars = existing_task_definition_config._replace(
        sidecars=[],
    ) == desired_task_definition_config._replace(
        sidecars=[],
    )
    if not match_without_sidecars:
        return False

    # Just match sidecars on certain fields
    if not [
        (
            sidecar["name"],
            sidecar["image"],
            sidecar.get("environment", []),
            sidecar.get("secrets", []),
        )
        for sidecar in existing_task_definition_config.sidecars
    ] == [
        (
            sidecar["name"],
            sidecar["image"],
            sidecar.get("environment", []),
            sidecar.get("secrets", []),
        )
        for sidecar in desired_task_definition_config.sidecars
    ]:
        return False

    return True
