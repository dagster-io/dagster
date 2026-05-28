import json
import logging
from typing import TYPE_CHECKING, Any

from dagster.components.core.load_defs import get_plugin_component_jsons_for_code_location

if TYPE_CHECKING:
    from dagster_graphql.schema.component_types import (
        GrapheneComponentTypeInfo,
        GrapheneComponentTypes,
    )
    from dagster_graphql.schema.errors import GrapheneRepositoryLocationNotFound
    from dagster_graphql.schema.util import ResolveInfo

logger = logging.getLogger("dagster")


def _parse_schema(schema_field: Any) -> Any:
    """The metadata stores the JSON schema as a JSON-encoded string.

    Parse it back to a JSON-shaped value for GraphQL clients so they don't
    double-decode. Returns ``None`` if the field is missing or empty.
    """
    if not schema_field:
        return None
    if isinstance(schema_field, str):
        try:
            return json.loads(schema_field)
        except json.JSONDecodeError:
            logger.warning(
                "Failed to JSON-decode component schema metadata; returning None.",
                exc_info=True,
            )
            return None
    return schema_field


def _to_component_type_info(component_json: dict) -> "GrapheneComponentTypeInfo":
    from dagster_graphql.schema.component_types import GrapheneComponentTypeInfo

    schema = _parse_schema(component_json.get("schema"))
    return GrapheneComponentTypeInfo(
        name=component_json["name"],
        schema=schema,
        description=component_json.get("description"),
        owners=component_json.get("owners"),
        tags=component_json.get("tags"),
    )


def get_component_types_for_location(
    graphene_info: "ResolveInfo", location_name: str
) -> "GrapheneComponentTypes | GrapheneRepositoryLocationNotFound":
    from dagster_graphql.schema.component_types import GrapheneComponentTypes
    from dagster_graphql.schema.errors import GrapheneRepositoryLocationNotFound

    context = graphene_info.context
    if not context.has_code_location(location_name):
        return GrapheneRepositoryLocationNotFound(location_name=location_name)

    code_location = context.get_code_location(location_name)
    component_jsons = get_plugin_component_jsons_for_code_location(code_location)
    component_types = [_to_component_type_info(cj) for cj in component_jsons]
    component_types.sort(key=lambda c: c.name)
    return GrapheneComponentTypes(locationName=location_name, componentTypes=component_types)
