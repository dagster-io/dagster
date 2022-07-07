import hashlib
import json
import os
import textwrap
from typing import AbstractSet, Any, Callable, Dict, Mapping, Optional, Sequence, Set, Tuple

from dagster_dbt.cli.types import DbtCliOutput
from dagster_dbt.cli.utils import execute_cli
from dagster_dbt.types import DbtOutput
from dagster_dbt.utils import generate_events

from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetsDefinition,
    In,
    MetadataValue,
    Nothing,
    Out,
    Output,
    PartitionsDefinition,
    SolidExecutionContext,
    TableColumn,
    TableSchema,
)
from dagster import _check as check
from dagster import get_dagster_logger, op
from dagster.core.definitions.events import CoercibleToAssetKeyPrefix
from dagster.core.definitions.load_assets_from_modules import prefix_assets
from dagster.core.definitions.metadata import RawMetadataValue
from dagster.core.errors import DagsterInvalidSubsetError
from dagster.utils.backcompat import experimental_arg_warning


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
        json_log_format=True,
        capture_logs=True,
    )
    manifest_path = os.path.join(target_dir, "manifest.json")
    with open(manifest_path, "r", encoding="utf8") as f:
        return json.load(f), cli_output


def _select_unique_ids_from_manifest_json(
    manifest_json: Mapping[str, Any], select: str
) -> AbstractSet[str]:
    """Method to apply a selection string to an existing manifest.json file."""
    try:
        import dbt.graph.cli as graph_cli
        import dbt.graph.selector as graph_selector
        from dbt.contracts.graph.manifest import Manifest
        from networkx import DiGraph
    except ImportError as e:
        raise check.CheckError(
            "In order to use the `select` argument on load_assets_from_dbt_manifest, you must have"
            "`dbt-core >= 1.0.0` and `networkx` installed."
        ) from e

    class _DictShim(dict):
        """Shim to enable hydrating a dictionary into a dot-accessible object"""

        def __getattr__(self, item):
            ret = super().get(item)
            # allow recursive access e.g. foo.bar.baz
            return _DictShim(ret) if isinstance(ret, dict) else ret

    # generate a dbt-compatible graph from the existing child map
    graph = graph_selector.Graph(DiGraph(incoming_graph_data=manifest_json["child_map"]))
    manifest = Manifest(
        # dbt expects dataclasses that can be accessed with dot notation, not bare dictionaries
        nodes={unique_id: _DictShim(info) for unique_id, info in manifest_json["nodes"].items()},
        sources={
            unique_id: _DictShim(info) for unique_id, info in manifest_json["sources"].items()
        },
    )

    # create a parsed selection from the select string
    parsed_spec = graph_cli.parse_union([select], True)

    # execute this selection against the graph
    selector = graph_selector.NodeSelector(graph, manifest)
    selected, _ = selector.select_nodes(parsed_spec)
    if len(selected) == 0:
        raise DagsterInvalidSubsetError(f"No dbt models match the selection string '{select}'.")
    return selected


def _get_node_name(node_info: Mapping[str, Any]):
    return "__".join([node_info["resource_type"], node_info["package_name"], node_info["name"]])


def _get_node_asset_key(node_info: Mapping[str, Any]) -> AssetKey:
    """By default:

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


def _get_node_group_name(node_info: Mapping[str, Any]) -> Optional[str]:
    """A node's group name is subdirectory that it resides in"""
    fqn = node_info.get("fqn", [])
    # the first component is the package name, and the last component is the model name
    if len(fqn) < 3:
        return None
    return fqn[1]


def _get_node_description(node_info):
    code_block = textwrap.indent(node_info["raw_sql"], "    ")
    description_sections = [
        node_info["description"],
        f"#### Raw SQL:\n```\n{code_block}\n```",
    ]
    return "\n\n".join(filter(None, description_sections))


def _dbt_nodes_to_assets(
    dbt_nodes: Mapping[str, Any],
    select: str,
    selected_unique_ids: AbstractSet[str],
    runtime_metadata_fn: Optional[
        Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, RawMetadataValue]]
    ] = None,
    io_manager_key: Optional[str] = None,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey] = _get_node_asset_key,
    use_build_command: bool = False,
    partitions_def: Optional[PartitionsDefinition] = None,
    partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]] = None,
) -> AssetsDefinition:

    outs: Dict[str, Out] = {}
    group_names: Dict[AssetKey, str] = {}
    asset_ins: Dict[AssetKey, Tuple[str, In]] = {}

    asset_deps: Dict[AssetKey, Set[AssetKey]] = {}

    out_name_to_node_info: Dict[str, Mapping[str, Any]] = {}

    package_name = None
    for unique_id in selected_unique_ids:
        cur_asset_deps = set()
        node_info = dbt_nodes[unique_id]
        if node_info["resource_type"] != "model":
            continue
        package_name = node_info.get("package_name", package_name)

        for dep_name in node_info["depends_on"]["nodes"]:
            dep_type = dbt_nodes[dep_name]["resource_type"]
            # ignore seeds/snapshots/tests
            if dep_type not in ["source", "model"]:
                continue
            dep_asset_key = node_info_to_asset_key(dbt_nodes[dep_name])

            # if it's a source, it will be used as an input to this multi-asset
            if dep_type == "source":
                asset_ins[dep_asset_key] = (dep_name.replace(".", "_"), In(Nothing))

            # regardless of type, list this as a dependency for the current asset
            cur_asset_deps.add(dep_asset_key)

        # generate the Out that corresponds to this model
        node_name = node_info["name"]
        outs[node_name] = Out(
            description=_get_node_description(node_info),
            io_manager_key=io_manager_key,
            metadata=_get_node_metadata(node_info),
            is_required=False,
        )
        out_name_to_node_info[node_name] = node_info

        asset_key = node_info_to_asset_key(node_info)

        # set the asset dependencies for this asset
        asset_deps[asset_key] = cur_asset_deps

        # set the group for this asset
        group_name = _get_node_group_name(node_info)
        if group_name is not None:
            group_names[asset_key] = group_name

    # prevent op name collisions between multiple dbt multi-assets
    op_name = f"run_dbt_{package_name}"
    if select != "*":
        op_name += "_" + hashlib.md5(select.encode()).hexdigest()[-5:]

    @op(
        name=op_name,
        tags={"kind": "dbt"},
        ins=dict(asset_ins.values()),
        out=outs,
        required_resource_keys={"dbt"},
    )
    def dbt_op(context):
        dbt_output = None

        # clean up any run results from the last run
        context.resources.dbt.remove_run_results_json()

        # in the case that we're running everything, opt for the cleaner selection string
        if len(context.selected_output_names) == len(outs):
            subselect = select
        else:
            # for each output that we want to emit, translate to a dbt select string by converting
            # the out to it's corresponding fqn
            subselect = [
                ".".join(out_name_to_node_info[out_name]["fqn"])
                for out_name in context.selected_output_names
            ]

        try:
            # variables to pass into the command
            kwargs = {"select": subselect}
            if partition_key_to_vars_fn:
                kwargs["vars"] = partition_key_to_vars_fn(context.partition_key)

            if use_build_command:
                dbt_output = context.resources.dbt.build(**kwargs)
            else:
                dbt_output = context.resources.dbt.run(**kwargs)
        finally:
            # in the case that the project only partially runs successfully, still attempt to generate
            # events for the parts that were successful
            if dbt_output is None:
                dbt_output = DbtOutput(result=context.resources.dbt.get_run_results_json())

            # yield an Output for each materialization generated in the run
            for event in generate_events(
                dbt_output,
                node_info_to_asset_key=node_info_to_asset_key,
                manifest_json=context.resources.dbt.get_manifest_json(),
            ):
                # convert AssetMaterializations to outputs
                if isinstance(event, AssetMaterialization):
                    output_name = event.asset_key.path[-1]
                    if runtime_metadata_fn:
                        yield Output(
                            value=None,
                            output_name=output_name,
                            metadata=runtime_metadata_fn(
                                context, out_name_to_node_info[output_name]
                            ),
                        )
                    else:
                        yield Output(
                            value=None,
                            output_name=output_name,
                            metadata_entries=event.metadata_entries,
                        )
                # yield AssetObservations normally
                else:
                    yield event

    return AssetsDefinition(
        keys_by_input_name={
            input_name: asset_key for asset_key, (input_name, _) in asset_ins.items()
        },
        keys_by_output_name={
            output_name: node_info_to_asset_key(out_name_to_node_info[output_name])
            for output_name in outs.keys()
        },
        node_def=dbt_op,
        can_subset=True,
        asset_deps=asset_deps,
        group_names_by_key=group_names,
        partitions_def=partitions_def,
    )


def _get_node_metadata(node_info: Mapping[str, Any]) -> Mapping[str, Any]:
    metadata: Dict[str, Any] = {}
    columns = node_info.get("columns", [])
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


def load_assets_from_dbt_project(
    project_dir: str,
    profiles_dir: Optional[str] = None,
    target_dir: Optional[str] = None,
    select: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    source_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    runtime_metadata_fn: Optional[
        Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ] = None,
    io_manager_key: Optional[str] = None,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey] = _get_node_asset_key,
    use_build_command: bool = False,
    partitions_def: Optional[PartitionsDefinition] = None,
    partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]] = None,
) -> Sequence[AssetsDefinition]:
    """
    Loads a set of dbt models from a dbt project into Dagster assets.

    Creates one Dagster asset for each dbt model. All assets will be re-materialized using a single
    `dbt run` or `dbt build` command.

    Args:
        project_dir (Optional[str]): The directory containing the dbt project to load.
        profiles_dir (Optional[str]): The profiles directory to use for loading the DBT project.
            Defaults to a directory called "config" inside the project_dir.
        target_dir (Optional[str]): The target directory where dbt will place compiled artifacts.
            Defaults to "target" underneath the project_dir.
        select (Optional[str]): A dbt selection string for the models in a project that you want
            to include. Defaults to "*".
        key_prefix (Optional[Union[str, List[str]]]): A prefix to apply to all models in the dbt
            project. Does not apply to sources.
        source_key_prefix (Optional[Union[str, List[str]]]): A prefix to apply to all sources in the
            dbt project. Does not apply to models.
        runtime_metadata_fn: (Optional[Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]]):
            A function that will be run after any of the assets are materialized and returns
            metadata entries for the asset, to be displayed in the asset catalog for that run.
        io_manager_key (Optional[str]): The IO manager key that will be set on each of the returned
            assets. When other ops are downstream of the loaded assets, the IOManager specified
            here determines how the inputs to those ops are loaded. Defaults to "io_manager".
        node_info_to_asset_key: (Mapping[str, Any] -> AssetKey): A function that takes a dictionary
            of dbt metadata and returns the AssetKey that you want to represent a given model or
            source. By default: dbt model -> AssetKey([model_name]) and
            dbt source -> AssetKey([source_name, table_name])
        use_build_command (bool): Flag indicating if you want to use `dbt build` as the core computation
            for this asset, rather than `dbt run`.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the dbt assets.
        partition_key_to_vars_fn (Optional[str -> Dict[str, Any]]): A function to translate a given
            partition key (e.g. '2022-01-01') to a dictionary of vars to be passed into the dbt
            invocation (e.g. {"run_date": "2022-01-01"})

    """
    project_dir = check.str_param(project_dir, "project_dir")
    profiles_dir = check.opt_str_param(
        profiles_dir, "profiles_dir", os.path.join(project_dir, "config")
    )
    target_dir = check.opt_str_param(target_dir, "target_dir", os.path.join(project_dir, "target"))
    select = check.opt_str_param(select, "select", "*")

    manifest_json, cli_output = _load_manifest_for_project(
        project_dir, profiles_dir, target_dir, select
    )
    selected_unique_ids: Set[str] = set(
        filter(None, (line.get("unique_id") for line in cli_output.logs))
    )
    return load_assets_from_dbt_manifest(
        manifest_json=manifest_json,
        select=select,
        key_prefix=key_prefix,
        source_key_prefix=source_key_prefix,
        runtime_metadata_fn=runtime_metadata_fn,
        io_manager_key=io_manager_key,
        selected_unique_ids=selected_unique_ids,
        node_info_to_asset_key=node_info_to_asset_key,
        use_build_command=use_build_command,
        partitions_def=partitions_def,
        partition_key_to_vars_fn=partition_key_to_vars_fn,
    )


def load_assets_from_dbt_manifest(
    manifest_json: Mapping[str, Any],
    select: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    source_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    runtime_metadata_fn: Optional[
        Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ] = None,
    io_manager_key: Optional[str] = None,
    selected_unique_ids: Optional[AbstractSet[str]] = None,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey] = _get_node_asset_key,
    use_build_command: bool = False,
    partitions_def: Optional[PartitionsDefinition] = None,
    partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]] = None,
) -> Sequence[AssetsDefinition]:
    """
    Loads a set of dbt models, described in a manifest.json, into Dagster assets.

    Creates one Dagster asset for each dbt model. All assets will be re-materialized using a single
    `dbt run` command.

    Args:
        manifest_json (Optional[Mapping[str, Any]]): The contents of a DBT manifest.json, which contains
            a set of models to load into assets.
        select (Optional[str]): A dbt selection string for the models in a project that you want
            to include. Defaults to "*".
        key_prefix (Optional[Union[str, List[str]]]): A prefix to apply to all models in the dbt
            project. Does not apply to sources.
        source_key_prefix (Optional[Union[str, List[str]]]): A prefix to apply to all sources in the
            dbt project. Does not apply to models.
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
        use_build_command (bool): Flag indicating if you want to use `dbt build` as the core computation
            for this asset, rather than `dbt run`.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the dbt assets.
        partition_key_to_vars_fn (Optional[str -> Dict[str, Any]]): A function to translate a given
            partition key (e.g. '2022-01-01') to a dictionary of vars to be passed into the dbt
            invocation (e.g. {"run_date": "2022-01-01"})
    """
    check.dict_param(manifest_json, "manifest_json", key_type=str)
    if partitions_def:
        experimental_arg_warning("partitions_def", "load_assets_from_dbt_manifest")
    if partition_key_to_vars_fn:
        experimental_arg_warning("partition_key_to_vars_fn", "load_assets_from_dbt_manifest")
        check.invariant(
            partitions_def is not None,
            "Cannot supply a `partition_key_to_vars_fn` without a `partitions_def`.",
        )

    dbt_nodes = {**manifest_json["nodes"], **manifest_json["sources"]}

    if select is None:
        if selected_unique_ids:
            # generate selection string from unique ids
            select = " ".join(".".join(dbt_nodes[uid]["fqn"]) for uid in selected_unique_ids)
        else:
            # if no selection specified, default to "*"
            select = "*"
            selected_unique_ids = manifest_json["nodes"].keys()

    if selected_unique_ids is None:
        # must resolve the selection string using the existing manifest.json data (hacky)
        selected_unique_ids = _select_unique_ids_from_manifest_json(manifest_json, select)

    dbt_assets_def = _dbt_nodes_to_assets(
        dbt_nodes,
        runtime_metadata_fn=runtime_metadata_fn,
        io_manager_key=io_manager_key,
        select=select,
        selected_unique_ids=selected_unique_ids,
        node_info_to_asset_key=node_info_to_asset_key,
        use_build_command=use_build_command,
        partitions_def=partitions_def,
        partition_key_to_vars_fn=partition_key_to_vars_fn,
    )
    if source_key_prefix:
        if isinstance(source_key_prefix, str):
            source_key_prefix = [source_key_prefix]
        source_key_prefix = check.list_param(source_key_prefix, "source_key_prefix", of_type=str)
        input_key_replacements = {
            input_key: AssetKey(source_key_prefix + input_key.path)
            for input_key in dbt_assets_def.keys_by_input_name.values()
        }
        dbt_assets = [
            dbt_assets_def.with_prefix_or_group(input_asset_key_replacements=input_key_replacements)
        ]
    else:
        dbt_assets = [dbt_assets_def]

    if key_prefix:
        dbt_assets = prefix_assets(dbt_assets, key_prefix)
    return dbt_assets
