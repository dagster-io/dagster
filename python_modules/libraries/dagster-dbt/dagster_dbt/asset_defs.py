import json
import os
import subprocess
import textwrap
from typing import Any, Callable, List, Mapping, Optional

from dagster import AssetKey, OpDefinition, Output, SolidExecutionContext, check
from dagster.core.asset_defs import asset


def _load_manifest_for_project(
    project_dir: str, profiles_dir: str, target_dir: str, select: str
) -> Mapping[str, Any]:
    command_list = [
        "dbt",
        "ls",
        "--project-dir",
        project_dir,
        "--profiles-dir",
        profiles_dir,
        "--select",
        select,
        "--resource-type",
        "model",
    ]
    # running "dbt ls" regenerates the manifest.json, which includes a superset of the actual
    # "dbt ls" output
    subprocess.Popen(command_list, stdout=subprocess.PIPE).wait()
    manifest_path = os.path.join(target_dir, "manifest.json")
    with open(manifest_path, "r") as f:
        return json.load(f)


def _get_node_name(node_info: Mapping[str, Any]):
    return "__".join([node_info["resource_type"], node_info["package_name"], node_info["name"]])


def _dbt_node_to_asset(
    node_info: Mapping[str, Any],
    runtime_metadata_fn: Optional[
        Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ] = None,
    io_manager_key: Optional[str] = None,
) -> OpDefinition:
    code_block = textwrap.indent(node_info["raw_sql"], "    ")
    description_sections = [
        node_info["description"],
        "#### Columns:\n" + _columns_to_markdown(node_info["columns"])
        if len(node_info["columns"]) > 0
        else None,
        f"#### Raw SQL:\n```\n{code_block}\n```",
    ]
    description = "\n\n".join(filter(None, description_sections))

    @asset(
        name=node_info["name"],
        description=description,
        non_argument_deps={
            AssetKey(dep_name.split(".")[-1]) for dep_name in node_info["depends_on"]["nodes"]
        },
        required_resource_keys={"dbt"},
        io_manager_key=io_manager_key,
        compute_kind="dbt",
    )
    def _node_asset(context):
        context.resources.dbt.run(models=[".".join([node_info["package_name"], node_info["name"]])])
        if runtime_metadata_fn:
            metadata = runtime_metadata_fn(context, node_info)
            yield Output(None, metadata=metadata)
        else:
            yield Output(None)

    return _node_asset


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
) -> List[OpDefinition]:
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
    """
    check.str_param(project_dir, "project_dir")
    profiles_dir = check.opt_str_param(
        profiles_dir, "profiles_dir", os.path.join(project_dir, "config")
    )
    target_dir = check.opt_str_param(target_dir, "target_dir", os.path.join(project_dir, "target"))

    manifest_json = _load_manifest_for_project(project_dir, profiles_dir, target_dir, select or "*")
    return load_assets_from_dbt_manifest(manifest_json, runtime_metadata_fn, io_manager_key)


def load_assets_from_dbt_manifest(
    manifest_json: Mapping[str, Any],
    runtime_metadata_fn: Optional[
        Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ] = None,
    io_manager_key: Optional[str] = None,
) -> List[OpDefinition]:
    """
    Loads a set of DBT models, described in a manifest.json, into Dagster assets.

    Creates one Dagster asset for each DBT model.

    Args:
        manifest_json (Optional[Mapping[str, Any]]): The contents of a DBT manifest.json, which contains
            a set of models to load into assets.
        runtime_metadata_fn: (Optional[Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]]):
            A function that will be run after any of the assets are materialized and returns
            metadata entries for the asset, to be displayed in the asset catalog for that run.
        io_manager_key (Optional[str]): The IO manager key that will be set on each of the returned
            assets. When other ops are downstream of the loaded assets, the IOManager specified
            here determines how the inputs to those ops are loaded. Defaults to "io_manager".
    """
    check.dict_param(manifest_json, "manifest_json", key_type=str)
    dbt_nodes = list(manifest_json["nodes"].values())
    return [
        _dbt_node_to_asset(
            node_info, runtime_metadata_fn=runtime_metadata_fn, io_manager_key=io_manager_key
        )
        for node_info in dbt_nodes
        if node_info["resource_type"] == "model"
    ]
