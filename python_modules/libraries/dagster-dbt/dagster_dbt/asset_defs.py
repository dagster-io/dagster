import json
import os
import subprocess
import textwrap
from typing import Any, Callable, List, Mapping, Optional, Sequence

from dagster import AssetKey, OpDefinition, Out, Output, SolidExecutionContext, check
from dagster.core.asset_defs import AssetsDefinition, multi_asset
from dagster_dbt.utils import generate_materializations


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


def _dbt_nodes_to_assets(
    node_infos: Sequence[Mapping[str, Any]],
    runtime_metadata_fn: Optional[
        Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ] = None,
    io_manager_key: Optional[str] = None,
) -> AssetsDefinition:
    outs = {}
    sources = set()
    out_name_to_node_info = {}
    for node_info in node_infos:
        node_name = node_info["name"]
        in_deps = []
        out_deps = []
        for dep in node_info["depends_on"]["nodes"]:
            dep_type = dep.split(".")[0]
            dep_name = dep.split(".")[-1]
            if dep_type == "source":
                sources.add(AssetKey(dep_name))
                in_deps.append(dep_name)
            elif dep_type == "model":
                out_deps.append(dep_name)
        code_block = textwrap.indent(node_info["raw_sql"], "    ")
        description_sections = [
            node_info["description"],
            "#### Columns:\n" + _columns_to_markdown(node_info["columns"])
            if len(node_info["columns"]) > 0
            else None,
            f"#### Raw SQL:\n```\n{code_block}\n```",
        ]
        description = "\n\n".join(filter(None, description_sections))

        outs[node_name] = Out(
            dagster_type=None,
            asset_key=AssetKey(node_name),
            in_deps=in_deps,
            out_deps=out_deps,
            description=description,
            io_manager_key=io_manager_key,
        )
        out_name_to_node_info[node_name] = node_info

    @multi_asset(
        name="dbt_project",
        non_argument_deps=sources,
        outs=outs,
        required_resource_keys={"dbt"},
        compute_kind="dbt",
    )
    def _dbt_project_multi_assset(context):
        dbt_output = context.resources.dbt.run()
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
) -> AssetsDefinition:
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
    return _dbt_nodes_to_assets(
        [node_info for node_info in dbt_nodes if node_info["resource_type"] == "model"],
        runtime_metadata_fn=runtime_metadata_fn,
        io_manager_key=io_manager_key,
    )
