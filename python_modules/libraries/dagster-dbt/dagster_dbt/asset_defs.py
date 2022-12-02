import hashlib
import json
import os
import textwrap
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

from dagster_dbt.cli.types import DbtCliOutput
from dagster_dbt.cli.utils import execute_cli
from dagster_dbt.types import DbtOutput
from dagster_dbt.utils import _get_input_name, _get_output_name, result_to_events

from dagster import (
    AssetKey,
    AssetsDefinition,
    In,
    MetadataValue,
    Nothing,
    Out,
    PartitionsDefinition,
    TableColumn,
    TableSchema,
)
from dagster import _check as check
from dagster import get_dagster_logger, op
from dagster._core.definitions.events import CoercibleToAssetKeyPrefix
from dagster._core.definitions.load_assets_from_modules import prefix_assets
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.errors import DagsterInvalidSubsetError
from dagster._legacy import SolidExecutionContext
from dagster._utils.backcompat import experimental_arg_warning


def _load_manifest_for_project(
    project_dir: str,
    profiles_dir: str,
    target_dir: str,
    select: str,
    exclude: str,
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
            "exclude": exclude,
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
    manifest_json: Mapping[str, Any], select: str, exclude: str
) -> AbstractSet[str]:
    """Method to apply a selection string to an existing manifest.json file."""
    try:
        import dbt.graph.cli as graph_cli
        import dbt.graph.selector as graph_selector
        from dbt.contracts.graph.manifest import Manifest
        from dbt.graph import SelectionSpec
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
        nodes={unique_id: _DictShim(info) for unique_id, info in manifest_json["nodes"].items()},  # type: ignore
        sources={
            unique_id: _DictShim(info) for unique_id, info in manifest_json["sources"].items()  # type: ignore
        },
        metrics={
            unique_id: _DictShim(info) for unique_id, info in manifest_json["metrics"].items()  # type: ignore
        },
        exposures={
            unique_id: _DictShim(info) for unique_id, info in manifest_json["exposures"].items()  # type: ignore
        },
    )

    # create a parsed selection from the select string
    parsed_spec: SelectionSpec = graph_cli.parse_union([select], True)

    if exclude:
        parsed_spec = graph_cli.SelectionDifference(
            components=[parsed_spec, graph_cli.parse_union([exclude], True)]
        )

    # execute this selection against the graph
    selector = graph_selector.NodeSelector(graph, manifest)
    selected, _ = selector.select_nodes(parsed_spec)
    if len(selected) == 0:
        raise DagsterInvalidSubsetError(f"No dbt models match the selection string '{select}'.")
    return selected


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


def _get_node_description(node_info, display_raw_sql):
    code_block = textwrap.indent(node_info.get("raw_sql") or node_info.get("raw_code", ""), "    ")
    description_sections = [
        node_info["description"] or f"dbt {node_info['resource_type']} {node_info['name']}",
    ]
    if display_raw_sql:
        description_sections.append(f"#### Raw SQL:\n```\n{code_block}\n```")
    return "\n\n".join(filter(None, description_sections))


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


def _get_deps(
    dbt_nodes: Mapping[str, Any],
    selected_unique_ids: AbstractSet[str],
    asset_resource_types: List[str],
) -> Mapping[str, FrozenSet[str]]:
    def _replaceable_node(node_info):
        # some nodes exist inside the dbt graph but are not assets
        resource_type = node_info["resource_type"]
        if resource_type == "metric":
            return True
        if (
            resource_type == "model"
            and node_info.get("config", {}).get("materialized") == "ephemeral"
        ):
            return True
        return False

    def _valid_parent_node(node_info):
        # sources are valid parents, but not assets
        return node_info["resource_type"] in asset_resource_types + ["source"]

    asset_deps: Dict[str, Set[str]] = {}
    for unique_id in selected_unique_ids:
        node_info = dbt_nodes[unique_id]
        node_resource_type = node_info["resource_type"]

        # skip non-assets, such as metrics, tests, and ephemeral models
        if _replaceable_node(node_info) or node_resource_type not in asset_resource_types:
            continue

        asset_deps[unique_id] = set()
        for parent_unique_id in node_info["depends_on"]["nodes"]:
            parent_node_info = dbt_nodes[parent_unique_id]
            # for metrics or ephemeral dbt models, BFS to find valid parents
            if _replaceable_node(parent_node_info):
                visited = set()
                replaced_parent_ids = set()
                queue = parent_node_info["depends_on"]["nodes"]
                while queue:
                    candidate_parent_id = queue.pop()
                    if candidate_parent_id in visited:
                        continue
                    visited.add(candidate_parent_id)

                    candidate_parent_info = dbt_nodes[candidate_parent_id]
                    if _replaceable_node(candidate_parent_info):
                        queue.extend(candidate_parent_info["depends_on"]["nodes"])
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


def _get_asset_deps(
    dbt_nodes, deps, node_info_to_asset_key, node_info_to_group_fn, io_manager_key, display_raw_sql
) -> Tuple[
    Dict[AssetKey, Set[AssetKey]],
    Dict[AssetKey, Tuple[str, In]],
    Dict[AssetKey, Tuple[str, Out]],
    Dict[AssetKey, str],
    Dict[str, List[str]],
    Dict[str, Dict[str, Any]],
]:
    asset_deps: Dict[AssetKey, Set[AssetKey]] = {}
    asset_ins: Dict[AssetKey, Tuple[str, In]] = {}
    asset_outs: Dict[AssetKey, Tuple[str, Out]] = {}

    # These dicts could be refactored as a single dict, mapping from output name to arbitrary
    # metadata that we need to store for reference.
    group_names_by_key: Dict[AssetKey, str] = {}
    fqns_by_output_name: Dict[str, List[str]] = {}
    metadata_by_output_name: Dict[str, Dict[str, Any]] = {}

    for unique_id, parent_unique_ids in deps.items():
        node_info = dbt_nodes[unique_id]

        output_name = _get_output_name(node_info)
        fqns_by_output_name[output_name] = node_info["fqn"]

        metadata_by_output_name[output_name] = {
            key: node_info[key] for key in ["unique_id", "resource_type"]
        }

        asset_key = node_info_to_asset_key(node_info)

        asset_deps[asset_key] = set()

        asset_outs[asset_key] = (
            output_name,
            Out(
                io_manager_key=io_manager_key,
                description=_get_node_description(node_info, display_raw_sql),
                metadata=_get_node_metadata(node_info),
                is_required=False,
                dagster_type=Nothing,
                code_version=hashlib.sha1(
                    (node_info.get("raw_sql") or node_info.get("raw_code", "")).encode("utf-8")
                ).hexdigest(),
            ),
        )

        group_name = node_info_to_group_fn(node_info)
        if group_name is not None:
            group_names_by_key[asset_key] = group_name

        for parent_unique_id in parent_unique_ids:
            parent_node_info = dbt_nodes[parent_unique_id]
            parent_asset_key = node_info_to_asset_key(parent_node_info)

            asset_deps[asset_key].add(parent_asset_key)

            # if this parent is not one of the selected nodes, it's an input
            if parent_unique_id not in deps:
                input_name = _get_input_name(parent_node_info)
                asset_ins[parent_asset_key] = (input_name, In(Nothing))

    return (
        asset_deps,
        asset_ins,
        asset_outs,
        group_names_by_key,
        fqns_by_output_name,
        metadata_by_output_name,
    )


def _get_dbt_op(
    op_name: str,
    ins: Mapping[str, In],
    outs: Mapping[str, Out],
    select: str,
    exclude: str,
    use_build_command: bool,
    fqns_by_output_name: Mapping[str, List[str]],
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey],
    partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]],
    runtime_metadata_fn: Optional[
        Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, RawMetadataValue]]
    ],
):
    @op(
        name=op_name,
        tags={"kind": "dbt"},
        ins=ins,
        out=outs,
        required_resource_keys={"dbt"},
    )
    def _dbt_op(context):
        dbt_output = None

        # clean up any run results from the last run
        context.resources.dbt.remove_run_results_json()

        # in the case that we're running everything, opt for the cleaner selection string
        if len(context.selected_output_names) == len(outs):
            kwargs = {"select": select, "exclude": exclude}
        else:
            # for each output that we want to emit, translate to a dbt select string by converting
            # the out to its corresponding fqn
            kwargs = {
                "select": [
                    ".".join(fqns_by_output_name[output_name])
                    for output_name in context.selected_output_names
                ]
            }

        try:
            # variables to pass into the command
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

            manifest_json = context.resources.dbt.get_manifest_json()

            for result in dbt_output.result["results"]:
                if runtime_metadata_fn:
                    node_info = manifest_json["nodes"][result["unique_id"]]
                    extra_metadata = runtime_metadata_fn(context, node_info)
                else:
                    extra_metadata = None
                yield from result_to_events(
                    result=result,
                    docs_url=dbt_output.docs_url,
                    node_info_to_asset_key=node_info_to_asset_key,
                    manifest_json=manifest_json,
                    extra_metadata=extra_metadata,
                    generate_asset_outputs=True,
                )

    return _dbt_op


def _dbt_nodes_to_assets(
    dbt_nodes: Mapping[str, Any],
    select: str,
    exclude: str,
    selected_unique_ids: AbstractSet[str],
    project_id: str,
    runtime_metadata_fn: Optional[
        Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, RawMetadataValue]]
    ] = None,
    io_manager_key: Optional[str] = None,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey] = _get_node_asset_key,
    use_build_command: bool = False,
    partitions_def: Optional[PartitionsDefinition] = None,
    partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]] = None,
    node_info_to_group_fn: Callable[[Mapping[str, Any]], Optional[str]] = _get_node_group_name,
    display_raw_sql: bool = True,
) -> AssetsDefinition:
    if use_build_command:
        deps = _get_deps(
            dbt_nodes,
            selected_unique_ids,
            asset_resource_types=["model", "seed", "snapshot"],
        )
    else:
        deps = _get_deps(dbt_nodes, selected_unique_ids, asset_resource_types=["model"])

    asset_deps, asset_ins, asset_outs, group_names_by_key, fqns_by_output_name, _ = _get_asset_deps(
        dbt_nodes=dbt_nodes,
        deps=deps,
        node_info_to_asset_key=node_info_to_asset_key,
        node_info_to_group_fn=node_info_to_group_fn,
        io_manager_key=io_manager_key,
        display_raw_sql=display_raw_sql,
    )

    # prevent op name collisions between multiple dbt multi-assets
    op_name = f"run_dbt_{project_id}"
    if select != "*" or exclude:
        op_name += "_" + hashlib.md5(select.encode() + exclude.encode()).hexdigest()[-5:]

    dbt_op = _get_dbt_op(
        op_name=op_name,
        ins=dict(asset_ins.values()),
        outs=dict(asset_outs.values()),
        select=select,
        exclude=exclude,
        use_build_command=use_build_command,
        fqns_by_output_name=fqns_by_output_name,
        node_info_to_asset_key=node_info_to_asset_key,
        partition_key_to_vars_fn=partition_key_to_vars_fn,
        runtime_metadata_fn=runtime_metadata_fn,
    )

    return AssetsDefinition(
        keys_by_input_name={
            input_name: asset_key for asset_key, (input_name, _) in asset_ins.items()
        },
        keys_by_output_name={
            output_name: asset_key for asset_key, (output_name, _) in asset_outs.items()
        },
        node_def=dbt_op,
        can_subset=True,
        asset_deps=asset_deps,
        group_names_by_key=group_names_by_key,
        partitions_def=partitions_def,
    )


def load_assets_from_dbt_project(
    project_dir: str,
    profiles_dir: Optional[str] = None,
    target_dir: Optional[str] = None,
    select: Optional[str] = None,
    exclude: Optional[str] = None,
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
    node_info_to_group_fn: Callable[[Mapping[str, Any]], Optional[str]] = _get_node_group_name,
    display_raw_sql: Optional[bool] = None,
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
        exclude (Optional[str]): A dbt selection string for the models in a project that you want
            to exclude. Defaults to "".
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
        node_info_to_group_fn (Dict[str, Any] -> Optional[str]): A function that takes a
            dictionary of dbt node info and returns the group that this node should be assigned to.
        display_raw_sql (Optional[bool]): [Experimental] A flag to indicate if the raw sql associated
            with each model should be included in the asset description. For large projects, setting
            this flag to False is advised to reduce the size of the resulting snapshot.

    """
    project_dir = check.str_param(project_dir, "project_dir")
    profiles_dir = check.opt_str_param(
        profiles_dir, "profiles_dir", os.path.join(project_dir, "config")
    )
    target_dir = check.opt_str_param(target_dir, "target_dir", os.path.join(project_dir, "target"))
    select = check.opt_str_param(select, "select", "*")
    exclude = check.opt_str_param(exclude, "exclude", "")

    manifest_json, cli_output = _load_manifest_for_project(
        project_dir, profiles_dir, target_dir, select, exclude
    )
    selected_unique_ids: Set[str] = set(
        filter(None, (line.get("unique_id") for line in cli_output.logs))
    )
    return load_assets_from_dbt_manifest(
        manifest_json=manifest_json,
        select=select,
        exclude=exclude,
        key_prefix=key_prefix,
        source_key_prefix=source_key_prefix,
        runtime_metadata_fn=runtime_metadata_fn,
        io_manager_key=io_manager_key,
        selected_unique_ids=selected_unique_ids,
        node_info_to_asset_key=node_info_to_asset_key,
        use_build_command=use_build_command,
        partitions_def=partitions_def,
        partition_key_to_vars_fn=partition_key_to_vars_fn,
        node_info_to_group_fn=node_info_to_group_fn,
        display_raw_sql=display_raw_sql,
    )


def load_assets_from_dbt_manifest(
    manifest_json: Mapping[str, Any],
    select: Optional[str] = None,
    exclude: Optional[str] = None,
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
    node_info_to_group_fn: Callable[[Mapping[str, Any]], Optional[str]] = _get_node_group_name,
    display_raw_sql: Optional[bool] = None,
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
        exclude (Optional[str]): A dbt selection string for the models in a project that you want
            to exclude. Defaults to "".
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
        node_info_to_group_fn (Dict[str, Any] -> Optional[str]): A function that takes a
            dictionary of dbt node info and returns the group that this node should be assigned to.
        display_raw_sql (Optional[bool]): [Experimental] A flag to indicate if the raw sql associated
            with each model should be included in the asset description. For large projects, setting
            this flag to False is advised to reduce the size of the resulting snapshot.
    """
    check.mapping_param(manifest_json, "manifest_json", key_type=str)
    if partitions_def:
        experimental_arg_warning("partitions_def", "load_assets_from_dbt_manifest")
    if partition_key_to_vars_fn:
        experimental_arg_warning("partition_key_to_vars_fn", "load_assets_from_dbt_manifest")
        check.invariant(
            partitions_def is not None,
            "Cannot supply a `partition_key_to_vars_fn` without a `partitions_def`.",
        )
    if display_raw_sql is not None:
        experimental_arg_warning("display_raw_sql", "load_assets_from_dbt_manifest")
    display_raw_sql = check.opt_bool_param(display_raw_sql, "display_raw_sql", default=True)

    dbt_nodes = {**manifest_json["nodes"], **manifest_json["sources"], **manifest_json["metrics"]}

    if selected_unique_ids:
        select = (
            " ".join(".".join(dbt_nodes[uid]["fqn"]) for uid in selected_unique_ids)
            if select is None
            else select
        )
        exclude = "" if exclude is None else exclude
    else:
        select = select if select is not None else "*"
        exclude = exclude if exclude is not None else ""

        selected_unique_ids = _select_unique_ids_from_manifest_json(manifest_json, select, exclude)

    dbt_assets_def = _dbt_nodes_to_assets(
        dbt_nodes,
        runtime_metadata_fn=runtime_metadata_fn,
        io_manager_key=io_manager_key,
        select=select,
        exclude=exclude,
        selected_unique_ids=selected_unique_ids,
        project_id=manifest_json["metadata"]["project_id"][:5],
        node_info_to_asset_key=node_info_to_asset_key,
        use_build_command=use_build_command,
        partitions_def=partitions_def,
        partition_key_to_vars_fn=partition_key_to_vars_fn,
        node_info_to_group_fn=node_info_to_group_fn,
        display_raw_sql=display_raw_sql,
    )
    dbt_assets: Sequence[AssetsDefinition]
    if source_key_prefix:
        if isinstance(source_key_prefix, str):
            source_key_prefix = [source_key_prefix]
        source_key_prefix = check.list_param(source_key_prefix, "source_key_prefix", of_type=str)
        input_key_replacements = {
            input_key: AssetKey([*source_key_prefix, *input_key.path])
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
