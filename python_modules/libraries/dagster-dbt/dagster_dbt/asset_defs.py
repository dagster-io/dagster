import hashlib
import json
import os
from pathlib import Path
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

import dateutil
from dagster import (
    AssetCheckResult,
    AssetKey,
    AssetsDefinition,
    AutoMaterializePolicy,
    FreshnessPolicy,
    In,
    OpExecutionContext,
    Out,
    PartitionsDefinition,
    PermissiveConfig,
    _check as check,
    get_dagster_logger,
    op,
)
from dagster._annotations import deprecated_param
from dagster._core.definitions.events import (
    AssetMaterialization,
    AssetObservation,
    CoercibleToAssetKeyPrefix,
    Output,
)
from dagster._core.definitions.metadata import MetadataUserInput, RawMetadataValue
from dagster._core.errors import DagsterInvalidSubsetError
from dagster._utils.merger import deep_merge_dicts
from dagster._utils.warnings import (
    deprecation_warning,
    normalize_renamed_param,
)

from dagster_dbt.asset_utils import (
    default_asset_key_fn,
    default_auto_materialize_policy_fn,
    default_description_fn,
    default_freshness_policy_fn,
    default_group_from_dbt_resource_props,
    default_metadata_from_dbt_resource_props,
    get_asset_deps,
    get_deps,
)
from dagster_dbt.core.resources import DbtCliClient
from dagster_dbt.core.resources_v2 import DbtCliResource
from dagster_dbt.core.types import DbtCliOutput
from dagster_dbt.core.utils import build_command_args_from_flags, execute_cli
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_dbt.errors import DagsterDbtError
from dagster_dbt.types import DbtOutput
from dagster_dbt.utils import (
    ASSET_RESOURCE_TYPES,
    output_name_fn,
    result_to_events,
    select_unique_ids_from_manifest,
)


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


def _can_stream_events(dbt_resource: Union[DbtCliClient, DbtCliResource]) -> bool:
    """Check if the installed dbt version supports streaming events."""
    import dbt.version
    from packaging import version

    if version.parse(dbt.version.__version__) >= version.parse("1.4.0"):
        # The json log format is required for streaming events. DbtCliResource always uses this format, but
        # DbtCliClient has an option to disable it.
        if isinstance(dbt_resource, DbtCliResource):
            return True
        else:
            return dbt_resource._json_log_format  # noqa: SLF001
    else:
        return False


def _batch_event_iterator(
    context: OpExecutionContext,
    dbt_resource: DbtCliClient,
    use_build_command: bool,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey],
    runtime_metadata_fn: Optional[
        Callable[[OpExecutionContext, Mapping[str, Any]], Mapping[str, RawMetadataValue]]
    ],
    kwargs: Dict[str, Any],
) -> Iterator[Union[AssetObservation, AssetMaterialization, Output]]:
    """Yields events for a dbt cli invocation. Waits until the entire command has completed before
    emitting outputs.
    """
    # clean up any run results from the last run
    dbt_resource.remove_run_results_json()

    dbt_output: Optional[DbtOutput] = None
    try:
        if use_build_command:
            dbt_output = dbt_resource.build(**kwargs)
        else:
            dbt_output = dbt_resource.run(**kwargs)
    finally:
        # in the case that the project only partially runs successfully, still attempt to generate
        # events for the parts that were successful
        if dbt_output is None:
            dbt_output = DbtOutput(result=check.not_none(dbt_resource.get_run_results_json()))

        manifest_json = check.not_none(dbt_resource.get_manifest_json())

        dbt_output = check.not_none(dbt_output)
        for result in dbt_output.result["results"]:
            extra_metadata: Optional[Mapping[str, RawMetadataValue]] = None
            if runtime_metadata_fn:
                node_info = manifest_json["nodes"][result["unique_id"]]
                extra_metadata = runtime_metadata_fn(context, node_info)
            yield from result_to_events(
                result=result,
                docs_url=dbt_output.docs_url,
                node_info_to_asset_key=node_info_to_asset_key,
                manifest_json=manifest_json,
                extra_metadata=extra_metadata,
                generate_asset_outputs=True,
            )


def _events_for_structured_json_line(
    json_line: Mapping[str, Any],
    context: OpExecutionContext,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey],
    runtime_metadata_fn: Optional[
        Callable[[OpExecutionContext, Mapping[str, Any]], Mapping[str, RawMetadataValue]]
    ],
    manifest_json: Mapping[str, Any],
) -> Iterator[Union[AssetObservation, Output]]:
    """Parses a json line into a Dagster event. Attempts to replicate the behavior of result_to_events
    as closely as possible.
    """
    runtime_node_info = json_line.get("data", {}).get("node_info", {})
    if not runtime_node_info:
        return

    node_resource_type = runtime_node_info.get("resource_type")
    node_status = runtime_node_info.get("node_status")
    unique_id = runtime_node_info.get("unique_id")

    if not node_resource_type or not unique_id:
        return

    compiled_node_info = manifest_json["nodes"][unique_id]

    if node_resource_type in ASSET_RESOURCE_TYPES and node_status == "success":
        metadata = dict(
            runtime_metadata_fn(context, compiled_node_info) if runtime_metadata_fn else {}
        )
        started_at_str = runtime_node_info.get("node_started_at")
        finished_at_str = runtime_node_info.get("node_finished_at")
        if started_at_str is None or finished_at_str is None:
            return

        started_at = dateutil.parser.isoparse(started_at_str)  # type: ignore
        completed_at = dateutil.parser.isoparse(finished_at_str)  # type: ignore
        duration = completed_at - started_at
        metadata.update(
            {
                "Execution Started At": started_at.isoformat(timespec="seconds"),
                "Execution Completed At": completed_at.isoformat(timespec="seconds"),
                "Execution Duration": duration.total_seconds(),
            }
        )
        yield Output(
            value=None,
            output_name=output_name_fn(compiled_node_info),
            metadata=metadata,
        )
    elif node_resource_type == "test" and runtime_node_info.get("node_finished_at"):
        upstream_unique_ids = (
            manifest_json["nodes"][unique_id].get("depends_on", {}).get("nodes", [])
        )
        # tests can apply to multiple asset keys
        for upstream_id in upstream_unique_ids:
            # the upstream id can reference a node or a source
            upstream_node_info = manifest_json["nodes"].get(upstream_id) or manifest_json[
                "sources"
            ].get(upstream_id)
            if upstream_node_info is None:
                continue
            upstream_asset_key = node_info_to_asset_key(upstream_node_info)
            yield AssetObservation(
                asset_key=upstream_asset_key,
                metadata={
                    "Test ID": unique_id,
                    "Test Status": node_status,
                },
            )


def _stream_event_iterator(
    context: OpExecutionContext,
    dbt_resource: Union[DbtCliResource, DbtCliClient],
    use_build_command: bool,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey],
    runtime_metadata_fn: Optional[
        Callable[[OpExecutionContext, Mapping[str, Any]], Mapping[str, RawMetadataValue]]
    ],
    kwargs: Dict[str, Any],
    manifest_json: Mapping[str, Any],
) -> Iterator[Union[AssetObservation, Output, AssetCheckResult]]:
    """Yields events for a dbt cli invocation. Emits outputs as soon as the relevant dbt logs are
    emitted.
    """
    if isinstance(dbt_resource, DbtCliClient):
        for parsed_json_line in dbt_resource.cli_stream_json(
            command="build" if use_build_command else "run",
            **kwargs,
        ):
            yield from _events_for_structured_json_line(
                parsed_json_line,
                context,
                node_info_to_asset_key,
                runtime_metadata_fn,
                manifest_json,
            )
    else:
        if runtime_metadata_fn is not None:
            raise DagsterDbtError(
                "The runtime_metadata_fn argument on the load_assets_from_dbt_manifest and"
                " load_assets_from_dbt_project functions is not supported when using the"
                " DbtCliResource resource. Use the @dbt_assets decorator instead if you want"
                " control over what metadata is yielded at runtime."
            )

        class CustomDagsterDbtTranslator(DagsterDbtTranslator):
            @classmethod
            def get_asset_key(cls, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
                return node_info_to_asset_key(dbt_resource_props)

        cli_output = dbt_resource.cli(
            args=["build" if use_build_command else "run", *build_command_args_from_flags(kwargs)],
            manifest=manifest_json,
            dagster_dbt_translator=CustomDagsterDbtTranslator(),
        )
        yield from cli_output.stream()


class DbtOpConfig(PermissiveConfig):
    """Keyword arguments to pass to the underlying dbt command. Additional arguments not listed in the schema will
    be passed through as well, e.g. {'bool_flag': True, 'string_flag': 'hi'} will result in the flags
    '--bool_flag --string_flag hi' being passed to the dbt command.
    """

    select: Optional[str] = None
    exclude: Optional[str] = None
    vars: Optional[Dict[str, Any]] = None
    full_refresh: Optional[bool] = None


def _get_dbt_op(
    op_name: str,
    ins: Mapping[str, In],
    outs: Mapping[str, Out],
    select: str,
    exclude: str,
    use_build_command: bool,
    fqns_by_output_name: Mapping[str, List[str]],
    dbt_resource_key: str,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey],
    partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]],
    runtime_metadata_fn: Optional[
        Callable[[OpExecutionContext, Mapping[str, Any]], Mapping[str, RawMetadataValue]]
    ],
    manifest_json: Mapping[str, Any],
):
    @op(
        name=op_name,
        tags={"kind": "dbt"},
        ins=ins,
        out=outs,
        required_resource_keys={dbt_resource_key},
    )
    def _dbt_op(context, config: DbtOpConfig):
        dbt_resource: Union[DbtCliResource, DbtCliClient] = getattr(
            context.resources, dbt_resource_key
        )
        check.inst(
            dbt_resource,
            (DbtCliResource, DbtCliClient),
            "Resource with key 'dbt_resource_key' must be a DbtCliResource or DbtCliClient"
            f" object, but is a {type(dbt_resource)}",
        )

        kwargs: Dict[str, Any] = {}
        # in the case that we're running everything, opt for the cleaner selection string
        if len(context.selected_output_names) == len(outs):
            kwargs["select"] = select
            kwargs["exclude"] = exclude
        else:
            # for each output that we want to emit, translate to a dbt select string by converting
            # the out to its corresponding fqn
            kwargs["select"] = [
                ".".join(fqns_by_output_name[output_name])
                for output_name in context.selected_output_names
            ]
        # variables to pass into the command
        if partition_key_to_vars_fn:
            kwargs["vars"] = partition_key_to_vars_fn(context.partition_key)
        # merge in any additional kwargs from the config
        kwargs = deep_merge_dicts(kwargs, context.op_config)

        if _can_stream_events(dbt_resource):
            yield from _stream_event_iterator(
                context,
                dbt_resource,
                use_build_command,
                node_info_to_asset_key,
                runtime_metadata_fn,
                kwargs,
                manifest_json=manifest_json,
            )
        else:
            if not isinstance(dbt_resource, DbtCliClient):
                check.failed(
                    "Chose batch event iterator, but it only works with DbtCliClient, and"
                    f" resource has type {type(dbt_resource)}"
                )
            yield from _batch_event_iterator(
                context,
                dbt_resource,
                use_build_command,
                node_info_to_asset_key,
                runtime_metadata_fn,
                kwargs,
            )

    return _dbt_op


def _dbt_nodes_to_assets(
    dbt_nodes: Mapping[str, Any],
    select: str,
    exclude: str,
    selected_unique_ids: AbstractSet[str],
    project_id: str,
    dbt_resource_key: str,
    manifest_json: Mapping[str, Any],
    op_name: Optional[str],
    runtime_metadata_fn: Optional[
        Callable[[OpExecutionContext, Mapping[str, Any]], Mapping[str, RawMetadataValue]]
    ],
    io_manager_key: Optional[str],
    use_build_command: bool,
    partitions_def: Optional[PartitionsDefinition],
    partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]],
    dagster_dbt_translator: DagsterDbtTranslator,
) -> AssetsDefinition:
    if use_build_command:
        deps = get_deps(
            dbt_nodes,
            selected_unique_ids,
            asset_resource_types=["model", "seed", "snapshot"],
        )
    else:
        deps = get_deps(dbt_nodes, selected_unique_ids, asset_resource_types=["model"])

    (
        asset_deps,
        asset_ins,
        asset_outs,
        group_names_by_key,
        freshness_policies_by_key,
        auto_materialize_policies_by_key,
        check_specs_by_output_name,
        fqns_by_output_name,
        _,
    ) = get_asset_deps(
        dbt_nodes=dbt_nodes,
        deps=deps,
        io_manager_key=io_manager_key,
        manifest=manifest_json,
        dagster_dbt_translator=dagster_dbt_translator,
    )

    # prevent op name collisions between multiple dbt multi-assets
    if not op_name:
        op_name = f"run_dbt_{project_id}"
        if select != "fqn:*" or exclude:
            op_name += "_" + hashlib.md5(select.encode() + exclude.encode()).hexdigest()[-5:]

    check_outs_by_output_name: Mapping[str, Out] = {}
    if check_specs_by_output_name:
        check_outs_by_output_name = {
            output_name: Out(dagster_type=None, is_required=False)
            for output_name in check_specs_by_output_name.keys()
        }

    dbt_op = _get_dbt_op(
        op_name=op_name,
        ins=dict(asset_ins.values()),
        outs={
            **dict(asset_outs.values()),
            **check_outs_by_output_name,
        },
        select=select,
        exclude=exclude,
        use_build_command=use_build_command,
        fqns_by_output_name=fqns_by_output_name,
        dbt_resource_key=dbt_resource_key,
        node_info_to_asset_key=dagster_dbt_translator.get_asset_key,
        partition_key_to_vars_fn=partition_key_to_vars_fn,
        runtime_metadata_fn=runtime_metadata_fn,
        manifest_json=manifest_json,
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
        freshness_policies_by_key=freshness_policies_by_key,
        auto_materialize_policies_by_key=auto_materialize_policies_by_key,
        check_specs_by_output_name=check_specs_by_output_name,
        partitions_def=partitions_def,
    )


def load_assets_from_dbt_project(
    project_dir: str,
    profiles_dir: Optional[str] = None,
    *,
    select: Optional[str] = None,
    exclude: Optional[str] = None,
    dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
    io_manager_key: Optional[str] = None,
    target_dir: Optional[str] = None,
    # All arguments below are deprecated
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    source_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    op_name: Optional[str] = None,
    runtime_metadata_fn: Optional[
        Callable[[OpExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ] = None,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey] = default_asset_key_fn,
    use_build_command: bool = True,
    partitions_def: Optional[PartitionsDefinition] = None,
    partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]] = None,
    node_info_to_group_fn: Callable[
        [Mapping[str, Any]], Optional[str]
    ] = default_group_from_dbt_resource_props,
    node_info_to_freshness_policy_fn: Callable[
        [Mapping[str, Any]], Optional[FreshnessPolicy]
    ] = default_freshness_policy_fn,
    node_info_to_auto_materialize_policy_fn: Callable[
        [Mapping[str, Any]], Optional[AutoMaterializePolicy]
    ] = default_auto_materialize_policy_fn,
    node_info_to_definition_metadata_fn: Callable[
        [Mapping[str, Any]], Mapping[str, MetadataUserInput]
    ] = default_metadata_from_dbt_resource_props,
    display_raw_sql: Optional[bool] = None,
    dbt_resource_key: str = "dbt",
) -> Sequence[AssetsDefinition]:
    """Loads a set of dbt models from a dbt project into Dagster assets.

    Creates one Dagster asset for each dbt model. All assets will be re-materialized using a single
    `dbt run` or `dbt build` command.

    When searching for more flexibility in defining the computations that materialize your
    dbt assets, we recommend that you use :py:class:`~dagster_dbt.dbt_assets`.

    Args:
        project_dir (Optional[str]): The directory containing the dbt project to load.
        profiles_dir (Optional[str]): The profiles directory to use for loading the DBT project.
            Defaults to a directory called "config" inside the project_dir.
        target_dir (Optional[str]): The target directory where dbt will place compiled artifacts.
            Defaults to "target" underneath the project_dir.
        select (Optional[str]): A dbt selection string for the models in a project that you want
            to include. Defaults to `"fqn:*"`.
        exclude (Optional[str]): A dbt selection string for the models in a project that you want
            to exclude. Defaults to "".
        dagster_dbt_translator (Optional[DagsterDbtTranslator]): Allows customizing how to map
            dbt models, seeds, etc. to asset keys and asset metadata.
        key_prefix (Optional[Union[str, List[str]]]): [Deprecated] A key prefix to apply to all assets loaded
            from the dbt project. Does not apply to input assets. Deprecated: use
            dagster_dbt_translator=KeyPrefixDagsterDbtTranslator(key_prefix=...) instead.
        source_key_prefix (Optional[Union[str, List[str]]]): [Deprecated] A key prefix to apply to all input
            assets for the set of assets loaded from the dbt project. Deprecated: use
            dagster_dbt_translator=KeyPrefixDagsterDbtTranslator(source_key_prefix=...) instead.
        op_name (Optional[str]): [Deprecated] Sets the name of the underlying Op that will generate the dbt assets.
            Deprecated: use the `@dbt_assets` decorator if you need to customize the op name.
        dbt_resource_key (Optional[str]): [Deprecated] The resource key that the dbt resource will be specified at.
            Defaults to "dbt". Deprecated: use the `@dbt_assets` decorator if you need to customize
            the resource key.
        runtime_metadata_fn (Optional[Callable[[OpExecutionContext, Mapping[str, Any]], Mapping[str, Any]]]):  [Deprecated]
            A function that will be run after any of the assets are materialized and returns
            metadata entries for the asset, to be displayed in the asset catalog for that run.
            Deprecated: use the @dbt_assets decorator if you need to customize runtime metadata.
        manifest_json (Optional[Mapping[str, Any]]): [Deprecated] Use the manifest argument instead.
        selected_unique_ids (Optional[Set[str]]): [Deprecated] The set of dbt unique_ids that you want to load
            as assets. Deprecated: use the select argument instead.
        node_info_to_asset_key (Mapping[str, Any] -> AssetKey): [Deprecated] A function that takes a dictionary
            of dbt node info and returns the AssetKey that you want to represent that node. By
            default, the asset key will simply be the name of the dbt model. Deprecated: instead,
            provide a custom DagsterDbtTranslator that overrides node_info_to_asset_key.
        use_build_command (bool): Flag indicating if you want to use `dbt build` as the core computation
            for this asset. Defaults to True. If set to False, then `dbt run` will be used, and
            seeds and snapshots won't be loaded as assets.
        partitions_def (Optional[PartitionsDefinition]): [Deprecated] Defines the set of partition keys that
            compose the dbt assets. Deprecated: use the @dbt_assets decorator to define partitioned
            dbt assets.
        partition_key_to_vars_fn (Optional[str -> Dict[str, Any]]): [Deprecated] A function to translate a given
            partition key (e.g. '2022-01-01') to a dictionary of vars to be passed into the dbt
            invocation (e.g. {"run_date": "2022-01-01"}). Deprecated: use the @dbt_assets decorator
            to define partitioned dbt assets.
        node_info_to_group_fn (Dict[str, Any] -> Optional[str]): [Deprecated] A function that takes a
            dictionary of dbt node info and returns the group that this node should be assigned to.
            Deprecated: instead, configure dagster groups on a dbt resource's meta field or assign
            dbt groups.
        node_info_to_freshness_policy_fn (Dict[str, Any] -> Optional[FreshnessPolicy]): [Deprecated] A function
            that takes a dictionary of dbt node info and optionally returns a FreshnessPolicy that
            should be applied to this node. By default, freshness policies will be created from
            config applied to dbt models, i.e.:
            `dagster_freshness_policy={"maximum_lag_minutes": 60, "cron_schedule": "0 9 * * *"}`
            will result in that model being assigned
            `FreshnessPolicy(maximum_lag_minutes=60, cron_schedule="0 9 * * *")`. Deprecated:
            instead, configure auto-materialize policies on a dbt resource's meta field.
        node_info_to_auto_materialize_policy_fn (Dict[str, Any] -> Optional[AutoMaterializePolicy]): [Deprecated]
            A function that takes a dictionary of dbt node info and optionally returns a AutoMaterializePolicy
            that should be applied to this node. By default, AutoMaterializePolicies will be created from
            config applied to dbt models, i.e.:
            `dagster_auto_materialize_policy={"type": "lazy"}` will result in that model being assigned
            `AutoMaterializePolicy.lazy()`. Deprecated: instead, configure auto-materialize
            policies on a dbt resource's meta field.
        node_info_to_definition_metadata_fn (Dict[str, Any] -> Optional[Dict[str, MetadataUserInput]]): [Deprecated]
            A function that takes a dictionary of dbt node info and optionally returns a dictionary
            of metadata to be attached to the corresponding definition. This is added to the default
            metadata assigned to the node, which consists of the node's schema (if present).
            Deprecated: instead, provide a custom DagsterDbtTranslator that overrides
            node_info_to_metadata.
        display_raw_sql (Optional[bool]): [Deprecated] A flag to indicate if the raw sql associated
            with each model should be included in the asset description. For large projects, setting
            this flag to False is advised to reduce the size of the resulting snapshot. Deprecated:
            instead, provide a custom DagsterDbtTranslator that overrides node_info_to_description.
    """
    project_dir = check.str_param(project_dir, "project_dir")
    profiles_dir = check.opt_str_param(
        profiles_dir, "profiles_dir", os.path.join(project_dir, "config")
    )
    target_dir = check.opt_str_param(target_dir, "target_dir", os.path.join(project_dir, "target"))
    select = check.opt_str_param(select, "select", "fqn:*")
    exclude = check.opt_str_param(exclude, "exclude", "")

    _raise_warnings_for_deprecated_args(
        "load_assets_from_dbt_manifest",
        selected_unique_ids=None,
        dbt_resource_key=dbt_resource_key,
        use_build_command=use_build_command,
        partitions_def=partitions_def,
        partition_key_to_vars_fn=partition_key_to_vars_fn,
        runtime_metadata_fn=runtime_metadata_fn,
        node_info_to_asset_key=node_info_to_asset_key,
        node_info_to_group_fn=node_info_to_group_fn,
        node_info_to_freshness_policy_fn=node_info_to_freshness_policy_fn,
        node_info_to_auto_materialize_policy_fn=node_info_to_auto_materialize_policy_fn,
        node_info_to_definition_metadata_fn=node_info_to_definition_metadata_fn,
    )

    manifest, cli_output = _load_manifest_for_project(
        project_dir, profiles_dir, target_dir, select, exclude
    )
    selected_unique_ids: Set[str] = set(
        filter(None, (line.get("unique_id") for line in cli_output.logs))
    )
    return _load_assets_from_dbt_manifest(
        manifest=manifest,
        select=select,
        exclude=exclude,
        key_prefix=key_prefix,
        source_key_prefix=source_key_prefix,
        dagster_dbt_translator=dagster_dbt_translator,
        op_name=op_name,
        runtime_metadata_fn=runtime_metadata_fn,
        io_manager_key=io_manager_key,
        selected_unique_ids=selected_unique_ids,
        node_info_to_asset_key=node_info_to_asset_key,
        use_build_command=use_build_command,
        partitions_def=partitions_def,
        partition_key_to_vars_fn=partition_key_to_vars_fn,
        node_info_to_auto_materialize_policy_fn=node_info_to_auto_materialize_policy_fn,
        node_info_to_group_fn=node_info_to_group_fn,
        node_info_to_freshness_policy_fn=node_info_to_freshness_policy_fn,
        node_info_to_definition_metadata_fn=node_info_to_definition_metadata_fn,
        display_raw_sql=display_raw_sql,
        dbt_resource_key=dbt_resource_key,
    )


@deprecated_param(
    param="manifest_json", breaking_version="0.21", additional_warn_text="Use manifest instead"
)
@deprecated_param(
    param="selected_unique_ids",
    breaking_version="0.21",
    additional_warn_text="Use the select parameter instead.",
)
@deprecated_param(
    param="dbt_resource_key",
    breaking_version="0.21",
    additional_warn_text=(
        "Use the `@dbt_assets` decorator if you need to customize your resource key."
    ),
)
@deprecated_param(
    param="use_build_command",
    breaking_version="0.21",
    additional_warn_text=(
        "Use the `@dbt_assets` decorator if you need to customize the underlying dbt commands."
    ),
)
@deprecated_param(
    param="partitions_def",
    breaking_version="0.21",
    additional_warn_text="Use the `@dbt_assets` decorator to define partitioned dbt assets.",
)
@deprecated_param(
    param="partition_key_to_vars_fn",
    breaking_version="0.21",
    additional_warn_text="Use the `@dbt_assets` decorator to define partitioned dbt assets.",
)
@deprecated_param(
    param="runtime_metadata_fn",
    breaking_version="0.21",
    additional_warn_text=(
        "Use the `@dbt_assets` decorator if you need to customize runtime metadata."
    ),
)
def load_assets_from_dbt_manifest(
    manifest: Optional[Union[Path, Mapping[str, Any]]] = None,
    *,
    select: Optional[str] = None,
    exclude: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
    # All arguments below are deprecated
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    source_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    selected_unique_ids: Optional[AbstractSet[str]] = None,
    display_raw_sql: Optional[bool] = None,
    dbt_resource_key: str = "dbt",
    op_name: Optional[str] = None,
    manifest_json: Optional[Mapping[str, Any]] = None,
    use_build_command: bool = True,
    partitions_def: Optional[PartitionsDefinition] = None,
    partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]] = None,
    runtime_metadata_fn: Optional[
        Callable[[OpExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ] = None,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey] = default_asset_key_fn,
    node_info_to_group_fn: Callable[
        [Mapping[str, Any]], Optional[str]
    ] = default_group_from_dbt_resource_props,
    node_info_to_freshness_policy_fn: Callable[
        [Mapping[str, Any]], Optional[FreshnessPolicy]
    ] = default_freshness_policy_fn,
    node_info_to_auto_materialize_policy_fn: Callable[
        [Mapping[str, Any]], Optional[AutoMaterializePolicy]
    ] = default_auto_materialize_policy_fn,
    node_info_to_definition_metadata_fn: Callable[
        [Mapping[str, Any]], Mapping[str, MetadataUserInput]
    ] = default_metadata_from_dbt_resource_props,
) -> Sequence[AssetsDefinition]:
    """Loads a set of dbt models, described in a manifest.json, into Dagster assets.

    Creates one Dagster asset for each dbt model. All assets will be re-materialized using a single
    `dbt run` command.

    When searching for more flexibility in defining the computations that materialize your
    dbt assets, we recommend that you use :py:class:`~dagster_dbt.dbt_assets`.

    Args:
        manifest (Optional[Mapping[str, Any]]): The contents of a DBT manifest.json, which contains
            a set of models to load into assets.
        select (Optional[str]): A dbt selection string for the models in a project that you want
            to include. Defaults to `"fqn:*"`.
        exclude (Optional[str]): A dbt selection string for the models in a project that you want
            to exclude. Defaults to "".
        io_manager_key (Optional[str]): The IO manager key that will be set on each of the returned
            assets. When other ops are downstream of the loaded assets, the IOManager specified
            here determines how the inputs to those ops are loaded. Defaults to "io_manager".
        dagster_dbt_translator (Optional[DagsterDbtTranslator]): Allows customizing how to map
            dbt models, seeds, etc. to asset keys and asset metadata.
        key_prefix (Optional[Union[str, List[str]]]): [Deprecated] A key prefix to apply to all assets loaded
            from the dbt project. Does not apply to input assets. Deprecated: use
            dagster_dbt_translator=KeyPrefixDagsterDbtTranslator(key_prefix=...) instead.
        source_key_prefix (Optional[Union[str, List[str]]]): [Deprecated] A key prefix to apply to all input
            assets for the set of assets loaded from the dbt project. Deprecated: use
            dagster_dbt_translator=KeyPrefixDagsterDbtTranslator(source_key_prefix=...) instead.
        op_name (Optional[str]): [Deprecated] Sets the name of the underlying Op that will generate the dbt assets.
            Deprecated: use the `@dbt_assets` decorator if you need to customize the op name.
        dbt_resource_key (Optional[str]): [Deprecated] The resource key that the dbt resource will be specified at.
            Defaults to "dbt". Deprecated: use the `@dbt_assets` decorator if you need to customize
            the resource key.
        runtime_metadata_fn (Optional[Callable[[OpExecutionContext, Mapping[str, Any]], Mapping[str, Any]]]):  [Deprecated]
            A function that will be run after any of the assets are materialized and returns
            metadata entries for the asset, to be displayed in the asset catalog for that run.
            Deprecated: use the @dbt_assets decorator if you need to customize runtime metadata.
        selected_unique_ids (Optional[Set[str]]): [Deprecated] The set of dbt unique_ids that you want to load
            as assets. Deprecated: use the select argument instead.
        node_info_to_asset_key (Mapping[str, Any] -> AssetKey): [Deprecated] A function that takes a dictionary
            of dbt node info and returns the AssetKey that you want to represent that node. By
            default, the asset key will simply be the name of the dbt model.
        use_build_command (bool): Flag indicating if you want to use `dbt build` as the core computation
            for this asset. Defaults to True. If set to False, then `dbt run` will be used, and
            seeds and snapshots won't be loaded as assets.
        partitions_def (Optional[PartitionsDefinition]): [Deprecated] Defines the set of partition keys that
            compose the dbt assets. Deprecated: use the @dbt_assets decorator to define partitioned
            dbt assets.
        partition_key_to_vars_fn (Optional[str -> Dict[str, Any]]): [Deprecated] A function to translate a given
            partition key (e.g. '2022-01-01') to a dictionary of vars to be passed into the dbt
            invocation (e.g. {"run_date": "2022-01-01"}). Deprecated: use the @dbt_assets decorator
            to define partitioned dbt assets.
        node_info_to_group_fn (Dict[str, Any] -> Optional[str]): [Deprecated] A function that takes a
            dictionary of dbt node info and returns the group that this node should be assigned to.
            Deprecated: instead, configure dagster groups on a dbt resource's meta field or assign
            dbt groups.
        node_info_to_freshness_policy_fn (Dict[str, Any] -> Optional[FreshnessPolicy]): [Deprecated] A function
            that takes a dictionary of dbt node info and optionally returns a FreshnessPolicy that
            should be applied to this node. By default, freshness policies will be created from
            config applied to dbt models, i.e.:
            `dagster_freshness_policy={"maximum_lag_minutes": 60, "cron_schedule": "0 9 * * *"}`
            will result in that model being assigned
            `FreshnessPolicy(maximum_lag_minutes=60, cron_schedule="0 9 * * *")`. Deprecated:
            instead, configure auto-materialize policies on a dbt resource's meta field.
        node_info_to_auto_materialize_policy_fn (Dict[str, Any] -> Optional[AutoMaterializePolicy]): [Deprecated]
            A function that takes a dictionary of dbt node info and optionally returns a AutoMaterializePolicy
            that should be applied to this node. By default, AutoMaterializePolicies will be created from
            config applied to dbt models, i.e.:
            `dagster_auto_materialize_policy={"type": "lazy"}` will result in that model being assigned
            `AutoMaterializePolicy.lazy()`. Deprecated: instead, configure auto-materialize
            policies on a dbt resource's meta field.
        node_info_to_definition_metadata_fn (Dict[str, Any] -> Optional[Dict[str, MetadataUserInput]]): [Deprecated]
            A function that takes a dictionary of dbt node info and optionally returns a dictionary
            of metadata to be attached to the corresponding definition. This is added to the default
            metadata assigned to the node, which consists of the node's schema (if present).
            Deprecated: instead, provide a custom DagsterDbtTranslator that overrides
            node_info_to_metadata.
        display_raw_sql (Optional[bool]): [Deprecated] A flag to indicate if the raw sql associated
            with each model should be included in the asset description. For large projects, setting
            this flag to False is advised to reduce the size of the resulting snapshot. Deprecated:
            instead, provide a custom DagsterDbtTranslator that overrides node_info_to_description.
    """
    manifest = normalize_renamed_param(
        manifest,
        "manifest",
        manifest_json,
        "manifest_json",
    )
    manifest = cast(
        Union[Mapping[str, Any], Path], check.inst_param(manifest, "manifest", (Path, dict))
    )
    if isinstance(manifest, Path):
        manifest = cast(Mapping[str, Any], json.loads(manifest.read_bytes()))

    _raise_warnings_for_deprecated_args(
        "load_assets_from_dbt_manifest",
        selected_unique_ids=selected_unique_ids,
        dbt_resource_key=dbt_resource_key,
        use_build_command=use_build_command,
        partitions_def=partitions_def,
        partition_key_to_vars_fn=partition_key_to_vars_fn,
        runtime_metadata_fn=runtime_metadata_fn,
        node_info_to_asset_key=node_info_to_asset_key,
        node_info_to_group_fn=node_info_to_group_fn,
        node_info_to_freshness_policy_fn=node_info_to_freshness_policy_fn,
        node_info_to_auto_materialize_policy_fn=node_info_to_auto_materialize_policy_fn,
        node_info_to_definition_metadata_fn=node_info_to_definition_metadata_fn,
    )

    return _load_assets_from_dbt_manifest(
        manifest=manifest,
        select=select,
        exclude=exclude,
        io_manager_key=io_manager_key,
        dagster_dbt_translator=dagster_dbt_translator,
        key_prefix=key_prefix,
        source_key_prefix=source_key_prefix,
        selected_unique_ids=selected_unique_ids,
        display_raw_sql=display_raw_sql,
        dbt_resource_key=dbt_resource_key,
        op_name=op_name,
        use_build_command=use_build_command,
        partitions_def=partitions_def,
        partition_key_to_vars_fn=partition_key_to_vars_fn,
        runtime_metadata_fn=runtime_metadata_fn,
        node_info_to_asset_key=node_info_to_asset_key,
        node_info_to_group_fn=node_info_to_group_fn,
        node_info_to_freshness_policy_fn=node_info_to_freshness_policy_fn,
        node_info_to_auto_materialize_policy_fn=node_info_to_auto_materialize_policy_fn,
        node_info_to_definition_metadata_fn=node_info_to_definition_metadata_fn,
    )


def _load_assets_from_dbt_manifest(
    manifest: Mapping[str, Any],
    select: Optional[str],
    exclude: Optional[str],
    io_manager_key: Optional[str],
    dagster_dbt_translator: Optional[DagsterDbtTranslator],
    key_prefix: Optional[CoercibleToAssetKeyPrefix],
    source_key_prefix: Optional[CoercibleToAssetKeyPrefix],
    selected_unique_ids: Optional[AbstractSet[str]],
    display_raw_sql: Optional[bool],
    dbt_resource_key: str,
    op_name: Optional[str],
    use_build_command: bool,
    partitions_def: Optional[PartitionsDefinition],
    partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]],
    runtime_metadata_fn: Optional[
        Callable[[OpExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ],
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey],
    node_info_to_group_fn: Callable[[Mapping[str, Any]], Optional[str]],
    node_info_to_freshness_policy_fn: Callable[[Mapping[str, Any]], Optional[FreshnessPolicy]],
    node_info_to_auto_materialize_policy_fn: Callable[
        [Mapping[str, Any]], Optional[AutoMaterializePolicy]
    ],
    node_info_to_definition_metadata_fn: Callable[
        [Mapping[str, Any]], Mapping[str, MetadataUserInput]
    ],
) -> Sequence[AssetsDefinition]:
    if partition_key_to_vars_fn:
        check.invariant(
            partitions_def is not None,
            "Cannot supply a `partition_key_to_vars_fn` without a `partitions_def`.",
        )

    dbt_resource_key = check.str_param(dbt_resource_key, "dbt_resource_key")

    dbt_nodes = {
        **manifest["nodes"],
        **manifest["sources"],
        **manifest["metrics"],
        **manifest["exposures"],
    }

    if selected_unique_ids:
        select = (
            " ".join(".".join(dbt_nodes[uid]["fqn"]) for uid in selected_unique_ids)
            if select is None
            else select
        )
        exclude = "" if exclude is None else exclude
    else:
        select = select if select is not None else "fqn:*"
        exclude = exclude if exclude is not None else ""

        selected_unique_ids = select_unique_ids_from_manifest(
            select=select, exclude=exclude, manifest_json=manifest
        )
        if len(selected_unique_ids) == 0:
            raise DagsterInvalidSubsetError(f"No dbt models match the selection string '{select}'.")

    if dagster_dbt_translator is not None:
        check.invariant(
            node_info_to_asset_key == default_asset_key_fn,
            "Can't specify both dagster_dbt_translator and node_info_to_asset_key",
        )
        check.invariant(
            key_prefix is None,
            "Can't specify both dagster_dbt_translator and key_prefix",
        )
        check.invariant(
            source_key_prefix is None,
            "Can't specify both dagster_dbt_translator and source_key_prefix",
        )
        check.invariant(
            node_info_to_group_fn == default_group_from_dbt_resource_props,
            "Can't specify both dagster_dbt_translator and node_info_to_group_fn",
        )
        check.invariant(
            display_raw_sql is None,
            "Can't specify both dagster_dbt_translator and display_raw_sql",
        )
        check.invariant(
            node_info_to_definition_metadata_fn is default_metadata_from_dbt_resource_props,
            "Can't specify both dagster_dbt_translator and node_info_to_definition_metadata_fn",
        )
    else:

        class CustomDagsterDbtTranslator(DagsterDbtTranslator):
            @classmethod
            def get_asset_key(cls, dbt_resource_props):
                base_key = node_info_to_asset_key(dbt_resource_props)
                if dbt_resource_props["resource_type"] == "source":
                    return base_key.with_prefix(source_key_prefix or [])
                else:
                    return base_key.with_prefix(key_prefix or [])

            @classmethod
            def get_metadata(cls, dbt_resource_props):
                return node_info_to_definition_metadata_fn(dbt_resource_props)

            @classmethod
            def get_description(cls, dbt_resource_props):
                return default_description_fn(
                    dbt_resource_props,
                    display_raw_sql=display_raw_sql if display_raw_sql is not None else True,
                )

            @classmethod
            def get_group_name(cls, dbt_resource_props):
                return node_info_to_group_fn(dbt_resource_props)

            @classmethod
            def get_freshness_policy(
                cls, dbt_resource_props: Mapping[str, Any]
            ) -> Optional[FreshnessPolicy]:
                return node_info_to_freshness_policy_fn(dbt_resource_props)

            @classmethod
            def get_auto_materialize_policy(
                cls, dbt_resource_props: Mapping[str, Any]
            ) -> Optional[AutoMaterializePolicy]:
                return node_info_to_auto_materialize_policy_fn(dbt_resource_props)

        dagster_dbt_translator = CustomDagsterDbtTranslator()

    dbt_assets_def = _dbt_nodes_to_assets(
        dbt_nodes,
        runtime_metadata_fn=runtime_metadata_fn,
        io_manager_key=io_manager_key,
        select=select,
        exclude=exclude,
        selected_unique_ids=selected_unique_ids,
        dbt_resource_key=dbt_resource_key,
        op_name=op_name,
        project_id=manifest["metadata"]["project_id"][:5],
        use_build_command=use_build_command,
        partitions_def=partitions_def,
        partition_key_to_vars_fn=partition_key_to_vars_fn,
        dagster_dbt_translator=dagster_dbt_translator,
        manifest_json=manifest,
    )

    return [dbt_assets_def]


def _raise_warnings_for_deprecated_args(
    public_fn_name: str,
    selected_unique_ids: Optional[AbstractSet[str]],
    dbt_resource_key: Optional[str],
    use_build_command: Optional[bool],
    partitions_def: Optional[PartitionsDefinition],
    partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]],
    runtime_metadata_fn: Optional[
        Callable[[OpExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ],
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey],
    node_info_to_group_fn: Callable[[Mapping[str, Any]], Optional[str]],
    node_info_to_freshness_policy_fn: Callable[[Mapping[str, Any]], Optional[FreshnessPolicy]],
    node_info_to_auto_materialize_policy_fn: Callable[
        [Mapping[str, Any]], Optional[AutoMaterializePolicy]
    ],
    node_info_to_definition_metadata_fn: Callable[
        [Mapping[str, Any]], Mapping[str, MetadataUserInput]
    ],
):
    if node_info_to_asset_key != default_asset_key_fn:
        deprecation_warning(
            f"The node_info_to_asset_key_fn arg of {public_fn_name}",
            "0.21",
            "Instead, provide a custom DagsterDbtTranslator that overrides get_asset_key.",
            stacklevel=4,
        )

    if node_info_to_group_fn != default_group_from_dbt_resource_props:
        deprecation_warning(
            f"The node_info_to_group_fn arg of {public_fn_name}",
            "0.21",
            "Instead, configure dagster groups on a dbt resource's meta field or assign dbt"
            " groups or provide a custom DagsterDbtTranslator that overrides get_group_name.",
            stacklevel=4,
        )

    if node_info_to_auto_materialize_policy_fn != default_auto_materialize_policy_fn:
        deprecation_warning(
            f"The node_info_to_auto_materialize_policy_fn arg of {public_fn_name}",
            "0.21",
            "Instead, configure Dagster auto-materialize policies on a dbt resource's meta field.",
            stacklevel=4,
        )

    if node_info_to_freshness_policy_fn != default_freshness_policy_fn:
        deprecation_warning(
            f"The node_info_to_freshness_policy_fn arg of {public_fn_name}",
            "0.21",
            "Instead, configure Dagster freshness policies on a dbt resource's meta field.",
            stacklevel=4,
        )

    if node_info_to_definition_metadata_fn != default_metadata_from_dbt_resource_props:
        deprecation_warning(
            f"The node_info_to_definition_metadata_fn arg of {public_fn_name}",
            "0.21",
            "Instead, provide a custom DagsterDbtTranslator that overrides get_metadata.",
            stacklevel=4,
        )
