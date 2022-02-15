import json
import os
import textwrap
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Set, Tuple, AbstractSet

from dagster import AssetKey, Out, Output, SolidExecutionContext, check, get_dagster_logger
from dagster.core.asset_defs import AssetsDefinition, multi_asset
from dagster_dbt.utils import generate_materializations
from dagster_dbt.cli.types import DbtCliOutput
from dagster_dbt.cli.utils import execute_cli


def _load_manifest_for_project(
    project_dir: str, profiles_dir: str, target_dir: str, select: str
) -> Tuple[Mapping[str, Any], DbtCliOutput]:
    # running "dbt ls" regenerates the manifest.json, which includes a superset of the actual
    # "dbt ls" output
    cli_output = execute_cli(
        executable="dbt",
        command="ls",
        log=get_dagster_logger(),
        flags_dict={
            "project-dir": project_dir,
            "profiles-dir": profiles_dir,
            "select": select,
            "resource-type": "model",
            "output": "json",
        },
        warn_error=False,
        ignore_handled_error=False,
        target_path=target_dir,
    )
    manifest_path = os.path.join(target_dir, "manifest.json")
    with open(manifest_path, "r") as f:
        return json.load(f), cli_output


def _get_node_name(node_info: Mapping[str, Any]):
    return "__".join([node_info["resource_type"], node_info["package_name"], node_info["name"]])


def _get_node_asset_key(node_info):
    return AssetKey(node_info["name"])


def _dbt_nodes_to_assets(
    dbt_nodes: Mapping[str, Any],
    select: str,
    selected_unique_ids: AbstractSet[str] = None,
    runtime_metadata_fn: Optional[
        Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ] = None,
    io_manager_key: Optional[str] = None,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey] = _get_node_asset_key,
) -> AssetsDefinition:
    outs: Dict[str, Out] = {}
    sources: Set[AssetKey] = set()
    out_name_to_node_info: Dict[str, Mapping[str, Any]] = {}
    internal_asset_deps: Dict[str, Set[AssetKey]] = {}
    for unique_id, node_info in dbt_nodes.items():
        if unique_id not in selected_unique_ids:
            continue
        asset_deps = set()
        for dep_name in node_info["depends_on"]["nodes"]:
            dep_type = dbt_nodes[dep_name]["resource_type"]
            dep_asset_key = node_info_to_asset_key(dbt_nodes[dep_name])
            if dep_type == "source":
                sources.add(dep_asset_key)
            asset_deps.add(dep_asset_key)
        code_block = textwrap.indent(node_info["raw_sql"], "    ")
        description_sections = [
            node_info["description"],
            "#### Columns:\n" + _columns_to_markdown(node_info["columns"])
            if len(node_info["columns"]) > 0
            else None,
            f"#### Raw SQL:\n```\n{code_block}\n```",
        ]
        description = "\n\n".join(filter(None, description_sections))

        node_name = node_info["name"]
        outs[node_name] = Out(
            dagster_type=None,
            asset_key=node_info_to_asset_key(node_info),
            description=description,
            io_manager_key=io_manager_key,
        )
        out_name_to_node_info[node_name] = node_info
        internal_asset_deps[node_name] = asset_deps

    @multi_asset(
        name="dbt_project",
        non_argument_deps=sources,
        outs=outs,
        required_resource_keys={"dbt"},
        compute_kind="dbt",
        internal_asset_deps=internal_asset_deps,
    )
    def _dbt_project_multi_assset(context):
        dbt_output = context.resources.dbt.run(select=select)
        # yield an Output for each materialization generated in the run
        for materialization in generate_materializations(dbt_output):
            output_name = materialization.asset_key.path[-1]
            if runtime_metadata_fn:
                yield Output(
                    value=None,
                    output_name=output_name,
                    metadata=runtime_metadata_fn(context, out_name_to_node_info[output_name]),
                )
            else:
                yield Output(
                    value=None,
                    output_name=output_name,
                    metadata_entries=materialization.metadata_entries,
                )

    return _dbt_project_multi_assset


def _columns_to_markdown(columns: Mapping[str, Any]) -> str:
    return (
        textwrap.dedent(
            """
        | Name | Description |
        | - | - |
    """
        )
        + "\n".join([f"| {name} | {metadata['description']}" for name, metadata in columns.items()])
    )


def load_assets_from_dbt_project(
    project_dir: str,
    profiles_dir: Optional[str] = None,
    target_dir: Optional[str] = None,
    select: Optional[str] = None,
    runtime_metadata_fn: Optional[
        Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ] = None,
    io_manager_key: Optional[str] = None,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey] = _get_node_asset_key,
) -> Sequence[AssetsDefinition]:
    """
    Loads a set of DBT models from a DBT project into Dagster assets.

    Args:
        project_dir (Optional[str]): The directory containing the DBT project to load.
        profiles_dir (Optional[str]): The profiles directory to use for loading the DBT project.
            Defaults to a directory called "config" inside the project_dir.
        target_dir (Optional[str]): The target directory where DBT will place compiled artifacts.
            Defaults to "target" underneath the project_dir.
        select (str): A DBT selection string for the models in a project that you want to include.
            Defaults to "*".
        runtime_metadata_fn: (Optional[Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]]):
            A function that will be run after any of the assets are materialized and returns
            metadata entries for the asset, to be displayed in the asset catalog for that run.
        io_manager_key (Optional[str]): The IO manager key that will be set on each of the returned
            assets. When other ops are downstream of the loaded assets, the IOManager specified
            here determines how the inputs to those ops are loaded. Defaults to "io_manager".
        node_info_to_asset_key: (Mapping[str, Any] -> AssetKey): A function that takes a dictionary
            of dbt node info and returns the AssetKey that you want to represent that node. By
            default, the asset key will simply be the name of the dbt model.
    """
    check.str_param(project_dir, "project_dir")
    profiles_dir = check.opt_str_param(
        profiles_dir, "profiles_dir", os.path.join(project_dir, "config")
    )
    target_dir = check.opt_str_param(target_dir, "target_dir", os.path.join(project_dir, "target"))

    manifest_json, cli_output = _load_manifest_for_project(
        project_dir, profiles_dir, target_dir, select or "*"
    )
    selected_unique_ids: Set[str] = set(
        filter(None, (line.get("unique_id") for line in cli_output.logs))
    )

    dbt_nodes = manifest_json["nodes"]
    return [
        _dbt_nodes_to_assets(
            dbt_nodes,
            select=select or "*",
            selected_unique_ids=selected_unique_ids,
            runtime_metadata_fn=runtime_metadata_fn,
            io_manager_key=io_manager_key,
            node_info_to_asset_key=node_info_to_asset_key,
        ),
    ]


def load_assets_from_dbt_manifest(
    manifest_json: Mapping[str, Any],
    runtime_metadata_fn: Optional[
        Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ] = None,
    io_manager_key: Optional[str] = None,
    selected_unique_ids: Optional[AbstractSet[str]] = None,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey] = _get_node_asset_key,
) -> Sequence[AssetsDefinition]:
    """
    Loads a set of dbt models, described in a manifest.json, into Dagster assets.

    Creates one Dagster asset for each dbt model.

    Args:
        manifest_json (Optional[Mapping[str, Any]]): The contents of a DBT manifest.json, which contains
            a set of models to load into assets.
        runtime_metadata_fn: (Optional[Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]]):
            A function that will be run after any of the assets are materialized and returns
            metadata entries for the asset, to be displayed in the asset catalog for that run.
        io_manager_key (Optional[str]): The IO manager key that will be set on each of the returned
            assets. When other ops are downstream of the loaded assets, the IOManager specified
            here determines how the inputs to those ops are loaded. Defaults to "io_manager".
        selected_unique_ids (Optional[Set[str]]): The set of dbt unique_ids that you want to load
            as assets.
        node_info_to_asset_key: (Mapping[str, Any] -> AssetKey): A function that takes a dictionary
            of dbt node info and returns the AssetKey that you want to represent that node. By
            default, the asset key will simply be the name of the dbt model.
    """
    check.dict_param(manifest_json, "manifest_json", key_type=str)
    dbt_nodes = manifest_json["nodes"]
    selected_unique_ids = selected_unique_ids or set(
        unique_id
        for unique_id, node_info in dbt_nodes.items()
        if node_info["resource_type"] == "model"
    )
    # create a selection string by converting the unique ids to model names
    select = (
        "*"
        if selected_unique_ids is None
        else " ".join((uid.split(".")[-1] for uid in selected_unique_ids))
    )
    return [
        _dbt_nodes_to_assets(
            dbt_nodes,
            runtime_metadata_fn=runtime_metadata_fn,
            io_manager_key=io_manager_key,
            select=select,
            selected_unique_ids=selected_unique_ids,
            node_info_to_asset_key=node_info_to_asset_key,
        )
    ]
