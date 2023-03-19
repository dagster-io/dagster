import textwrap
from typing import AbstractSet, Any, Dict, FrozenSet, List, Mapping, Optional, Set

from dagster import AssetKey, FreshnessPolicy, MetadataValue, TableColumn, TableSchema

###################
# DEFAULT FUNCTIONS
###################


def default_asset_key_fn(node_info: Mapping[str, Any]) -> AssetKey:
    """Get the asset key for a dbt node.

    By default:
        dbt sources: a dbt source's key is the union of its source name and its table name
        dbt models: a dbt model's key is the union of its model name and any schema configured on
    the model itself.
    """
    if node_info["resource_type"] == "source":
        components = [node_info["source_name"], node_info["name"]]
    else:
        configured_schema = node_info["config"].get("schema")
        if configured_schema is not None:
            components = [configured_schema, node_info["name"]]
        else:
            components = [node_info["name"]]

    return AssetKey(components)


def default_metadata_fn(node_info: Mapping[str, Any]) -> Mapping[str, Any]:
    metadata: Dict[str, Any] = {}
    columns = node_info.get("columns", {})
    if len(columns) > 0:
        metadata["table_schema"] = MetadataValue.table_schema(
            TableSchema(
                columns=[
                    TableColumn(
                        name=column_name,
                        type=column_info.get("data_type") or "?",
                        description=column_info.get("description"),
                    )
                    for column_name, column_info in columns.items()
                ]
            )
        )
    return metadata


def default_group_fn(node_info: Mapping[str, Any]) -> Optional[str]:
    """A node's group name is subdirectory that it resides in."""
    fqn = node_info.get("fqn", [])
    # the first component is the package name, and the last component is the model name
    if len(fqn) < 3:
        return None
    return fqn[1]


def default_freshness_policy_fn(node_info: Mapping[str, Any]) -> Optional[FreshnessPolicy]:
    freshness_policy_config = node_info["config"].get("dagster_freshness_policy")
    if freshness_policy_config:
        return FreshnessPolicy(
            maximum_lag_minutes=float(freshness_policy_config["maximum_lag_minutes"]),
            cron_schedule=freshness_policy_config.get("cron_schedule"),
            cron_schedule_timezone=freshness_policy_config.get("cron_schedule_timezone"),
        )
    return None


def default_description_fn(node_info: Mapping[str, Any], display_raw_sql: bool = True):
    code_block = textwrap.indent(node_info.get("raw_sql") or node_info.get("raw_code", ""), "    ")
    description_sections = [
        node_info["description"] or f"dbt {node_info['resource_type']} {node_info['name']}",
    ]
    if display_raw_sql:
        description_sections.append(f"#### Raw SQL:\n```\n{code_block}\n```")
    return "\n\n".join(filter(None, description_sections))


###################
# DEPENDENCIES
###################


def is_non_asset_node(node_info: Mapping[str, Any]):
    # some nodes exist inside the dbt graph but are not assets
    resource_type = node_info["resource_type"]
    if resource_type == "metric":
        return True
    if resource_type == "model" and node_info.get("config", {}).get("materialized") == "ephemeral":
        return True
    return False


def get_deps(
    dbt_nodes: Mapping[str, Any],
    selected_unique_ids: AbstractSet[str],
    asset_resource_types: List[str],
) -> Mapping[str, FrozenSet[str]]:
    def _valid_parent_node(node_info):
        # sources are valid parents, but not assets
        return node_info["resource_type"] in asset_resource_types + ["source"]

    asset_deps: Dict[str, Set[str]] = {}
    for unique_id in selected_unique_ids:
        node_info = dbt_nodes[unique_id]
        node_resource_type = node_info["resource_type"]

        # skip non-assets, such as metrics, tests, and ephemeral models
        if is_non_asset_node(node_info) or node_resource_type not in asset_resource_types:
            continue

        asset_deps[unique_id] = set()
        for parent_unique_id in node_info.get("depends_on", {}).get("nodes", []):
            parent_node_info = dbt_nodes[parent_unique_id]
            # for metrics or ephemeral dbt models, BFS to find valid parents
            if is_non_asset_node(parent_node_info):
                visited = set()
                replaced_parent_ids = set()
                queue = parent_node_info.get("depends_on", {}).get("nodes", [])
                while queue:
                    candidate_parent_id = queue.pop()
                    if candidate_parent_id in visited:
                        continue
                    visited.add(candidate_parent_id)

                    candidate_parent_info = dbt_nodes[candidate_parent_id]
                    if is_non_asset_node(candidate_parent_info):
                        queue.extend(candidate_parent_info.get("depends_on", {}).get("nodes", []))
                    elif _valid_parent_node(candidate_parent_info):
                        replaced_parent_ids.add(candidate_parent_id)

                asset_deps[unique_id] |= replaced_parent_ids
            # ignore nodes which are not assets / sources
            elif _valid_parent_node(parent_node_info):
                asset_deps[unique_id].add(parent_unique_id)

    frozen_asset_deps = {
        unique_id: frozenset(parent_ids) for unique_id, parent_ids in asset_deps.items()
    }

    return frozen_asset_deps
