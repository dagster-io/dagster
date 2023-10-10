import hashlib
import textwrap
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    FrozenSet,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)

from dagster import (
    AssetCheckSpec,
    AssetKey,
    AssetsDefinition,
    AssetSelection,
    AutoMaterializePolicy,
    DagsterInvariantViolationError,
    FreshnessPolicy,
    In,
    MetadataValue,
    Nothing,
    Out,
    RunConfig,
    ScheduleDefinition,
    TableColumn,
    TableSchema,
    _check as check,
    define_asset_job,
)
from dagster._core.definitions.decorators.asset_decorator import (
    _validate_and_assign_output_names_to_check_specs,
)
from dagster._utils.merger import merge_dicts
from dagster._utils.warnings import deprecation_warning

from .utils import input_name_fn, output_name_fn

if TYPE_CHECKING:
    from .dagster_dbt_translator import (
        DagsterDbtTranslator,
        DagsterDbtTranslatorSettings,
        DbtManifestWrapper,
    )

MANIFEST_METADATA_KEY = "dagster_dbt/manifest"
DAGSTER_DBT_TRANSLATOR_METADATA_KEY = "dagster_dbt/dagster_dbt_translator"


def get_asset_key_for_model(dbt_assets: Sequence[AssetsDefinition], model_name: str) -> AssetKey:
    """Return the corresponding Dagster asset key for a dbt model.

    Args:
        dbt_assets (AssetsDefinition): An AssetsDefinition object produced by
            load_assets_from_dbt_project, load_assets_from_dbt_manifest, or @dbt_assets.
        model_name (str): The name of the dbt model.

    Returns:
        AssetKey: The corresponding Dagster asset key.

    Examples:
        .. code-block:: python

            from dagster import asset
            from dagster_dbt import dbt_assets, get_asset_key_for_model

            @dbt_assets(manifest=...)
            def all_dbt_assets():
                ...


            @asset(deps={get_asset_key_for_model([all_dbt_assets], "customers")})
            def cleaned_customers():
                ...
    """
    check.sequence_param(dbt_assets, "dbt_assets", of_type=AssetsDefinition)
    check.str_param(model_name, "model_name")

    manifest, dagster_dbt_translator = get_manifest_and_translator_from_dbt_assets(dbt_assets)

    matching_models = [
        value
        for value in manifest["nodes"].values()
        if value["name"] == model_name and value["resource_type"] == "model"
    ]

    if len(matching_models) == 0:
        raise KeyError(f"Could not find a dbt model with name: {model_name}")

    return dagster_dbt_translator.get_asset_key(next(iter(matching_models)))


def get_asset_keys_by_output_name_for_source(
    dbt_assets: Sequence[AssetsDefinition], source_name: str
) -> Mapping[str, AssetKey]:
    """Returns the corresponding Dagster asset keys for all tables in a dbt source.

    This is a convenience method that makes it easy to define a multi-asset that generates
    all the tables for a given dbt source.

    Args:
        source_name (str): The name of the dbt source.

    Returns:
        Mapping[str, AssetKey]: A mapping of the table name to corresponding Dagster asset key
            for all tables in the given dbt source.

    Examples:
        .. code-block:: python

            from dagster import AssetOut, multi_asset
            from dagster_dbt import dbt_assets, get_asset_keys_by_output_name_for_source

            @dbt_assets(manifest=...)
            def all_dbt_assets():
                ...

            @multi_asset(
                outs={
                    name: AssetOut(key=asset_key)
                    for name, asset_key in get_asset_keys_by_output_name_for_source(
                        [all_dbt_assets], "raw_data"
                    ).items()
                },
            )
            def upstream_python_asset():
                ...

    """
    check.sequence_param(dbt_assets, "dbt_assets", of_type=AssetsDefinition)
    check.str_param(source_name, "source_name")

    manifest, dagster_dbt_translator = get_manifest_and_translator_from_dbt_assets(dbt_assets)

    matching_nodes = [
        value for value in manifest["sources"].values() if value["source_name"] == source_name
    ]

    if len(matching_nodes) == 0:
        raise KeyError(f"Could not find a dbt source with name: {source_name}")

    return {
        output_name_fn(value): dagster_dbt_translator.get_asset_key(value)
        for value in matching_nodes
    }


def get_asset_key_for_source(dbt_assets: Sequence[AssetsDefinition], source_name: str) -> AssetKey:
    """Returns the corresponding Dagster asset key for a dbt source with a singular table.

    Args:
        source_name (str): The name of the dbt source.

    Raises:
        DagsterInvalidInvocationError: If the source has more than one table.

    Returns:
        AssetKey: The corresponding Dagster asset key.

    Examples:
        .. code-block:: python

            from dagster import asset
            from dagster_dbt import dbt_assets, get_asset_key_for_source

            @dbt_assets(manifest=...)
            def all_dbt_assets():
                ...

            @asset(key=get_asset_key_for_source([all_dbt_assets], "my_source"))
            def upstream_python_asset():
                ...
    """
    asset_keys_by_output_name = get_asset_keys_by_output_name_for_source(dbt_assets, source_name)

    if len(asset_keys_by_output_name) > 1:
        raise KeyError(
            f"Source {source_name} has more than one table:"
            f" {asset_keys_by_output_name.values()}. Use"
            " `get_asset_keys_by_output_name_for_source` instead to get all tables for a"
            " source."
        )

    return next(iter(asset_keys_by_output_name.values()))


def build_dbt_asset_selection(
    dbt_assets: Sequence[AssetsDefinition],
    dbt_select: str = "fqn:*",
    dbt_exclude: Optional[str] = None,
) -> AssetSelection:
    """Build an asset selection for a dbt selection string.

    See https://docs.getdbt.com/reference/node-selection/syntax#how-does-selection-work for
    more information.

    Args:
        dbt_select (str): A dbt selection string to specify a set of dbt resources.
        dbt_exclude (Optional[str]): A dbt selection string to exclude a set of dbt resources.

    Returns:
        AssetSelection: An asset selection for the selected dbt nodes.

    Examples:
        .. code-block:: python

            from dagster_dbt import dbt_assets, build_dbt_asset_selection

            @dbt_assets(manifest=...)
            def all_dbt_assets():
                ...

            # Select the dbt assets that have the tag "foo".
            foo_selection = build_dbt_asset_selection([dbt_assets], dbt_select="tag:foo")

            # Select the dbt assets that have the tag "foo" and all Dagster assets downstream
            # of them (dbt-related or otherwise)
            foo_and_downstream_selection = foo_selection.downstream()

    """
    manifest, dagster_dbt_translator = get_manifest_and_translator_from_dbt_assets(dbt_assets)
    from .dbt_manifest_asset_selection import DbtManifestAssetSelection

    return DbtManifestAssetSelection(
        manifest=manifest,
        dagster_dbt_translator=dagster_dbt_translator,
        select=dbt_select,
        exclude=dbt_exclude,
    )


def build_schedule_from_dbt_selection(
    dbt_assets: Sequence[AssetsDefinition],
    job_name: str,
    cron_schedule: str,
    dbt_select: str = "fqn:*",
    dbt_exclude: Optional[str] = None,
    tags: Optional[Mapping[str, str]] = None,
    config: Optional[RunConfig] = None,
    execution_timezone: Optional[str] = None,
) -> ScheduleDefinition:
    """Build a schedule to materialize a specified set of dbt resources from a dbt selection string.

    See https://docs.getdbt.com/reference/node-selection/syntax#how-does-selection-work for
    more information.

    Args:
        job_name (str): The name of the job to materialize the dbt resources.
        cron_schedule (str): The cron schedule to define the schedule.
        dbt_select (str): A dbt selection string to specify a set of dbt resources.
        dbt_exclude (Optional[str]): A dbt selection string to exclude a set of dbt resources.
        tags (Optional[Mapping[str, str]]): A dictionary of tags (string key-value pairs) to attach
            to the scheduled runs.
        config (Optional[RunConfig]): The config that parameterizes the execution of this schedule.
        execution_timezone (Optional[str]): Timezone in which the schedule should run.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".

    Returns:
        ScheduleDefinition: A definition to materialize the selected dbt resources on a cron schedule.

    Examples:
        .. code-block:: python

            from dagster_dbt import dbt_assets, build_schedule_from_dbt_selection

            @dbt_assets(manifest=...)
            def all_dbt_assets():
                ...

            daily_dbt_assets_schedule = build_schedule_from_dbt_selection(
                [all_dbt_assets],
                job_name="all_dbt_assets",
                cron_schedule="0 0 * * *",
                dbt_select="fqn:*",
            )
    """
    return ScheduleDefinition(
        cron_schedule=cron_schedule,
        job=define_asset_job(
            name=job_name,
            selection=build_dbt_asset_selection(
                dbt_assets,
                dbt_select=dbt_select,
                dbt_exclude=dbt_exclude,
            ),
            config=config,
            tags=tags,
        ),
        execution_timezone=execution_timezone,
    )


def get_manifest_and_translator_from_dbt_assets(
    dbt_assets: Sequence[AssetsDefinition],
) -> Tuple[Mapping[str, Any], "DagsterDbtTranslator"]:
    check.invariant(len(dbt_assets) == 1, "Exactly one dbt AssetsDefinition is required")
    dbt_assets_def = dbt_assets[0]
    metadata_by_key = dbt_assets_def.metadata_by_key or {}
    first_asset_key = next(iter(dbt_assets_def.metadata_by_key.keys()))
    first_metadata = metadata_by_key.get(first_asset_key, {})
    manifest_wrapper: Optional["DbtManifestWrapper"] = first_metadata.get(MANIFEST_METADATA_KEY)
    if manifest_wrapper is None:
        raise DagsterInvariantViolationError(
            f"Expected to find dbt manifest metadata on asset {first_asset_key.to_user_string()},"
            " but did not. Did you pass in assets that weren't generated by"
            " load_assets_from_dbt_project, load_assets_from_dbt_manifest, or @dbt_assets?"
        )

    dagster_dbt_translator = first_metadata.get(DAGSTER_DBT_TRANSLATOR_METADATA_KEY)
    if dagster_dbt_translator is None:
        raise DagsterInvariantViolationError(
            f"Expected to find dbt translator metadata on asset {first_asset_key.to_user_string()},"
            " but did not. Did you pass in assets that weren't generated by"
            " load_assets_from_dbt_project, load_assets_from_dbt_manifest, or @dbt_assets?"
        )

    return manifest_wrapper.manifest, dagster_dbt_translator


###################
# DEFAULT FUNCTIONS
###################


def default_asset_key_fn(dbt_resource_props: Mapping[str, Any]) -> AssetKey:
    """Get the asset key for a dbt node.

    By default, if the dbt node has a Dagster asset key configured in its metadata, then that is
    parsed and used.

    Otherwise:
        dbt sources: a dbt source's key is the union of its source name and its table name
        dbt models: a dbt model's key is the union of its model name and any schema configured on
            the model itself.
    """
    dagster_metadata = dbt_resource_props.get("meta", {}).get("dagster", {})
    asset_key_config = dagster_metadata.get("asset_key", [])
    if asset_key_config:
        return AssetKey(asset_key_config)

    if dbt_resource_props["resource_type"] == "source":
        components = [dbt_resource_props["source_name"], dbt_resource_props["name"]]
    else:
        configured_schema = dbt_resource_props["config"].get("schema")
        if configured_schema is not None:
            components = [configured_schema, dbt_resource_props["name"]]
        else:
            components = [dbt_resource_props["name"]]

    return AssetKey(components)


def default_metadata_from_dbt_resource_props(
    dbt_resource_props: Mapping[str, Any]
) -> Mapping[str, Any]:
    metadata: Dict[str, Any] = {}
    columns = dbt_resource_props.get("columns", {})
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


def default_group_from_dbt_resource_props(dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
    """Get the group name for a dbt node.

    If a Dagster group is configured in the metadata for the node, use that.

    Otherwise, if a dbt group is configured for the node, use that.
    """
    dagster_metadata = dbt_resource_props.get("meta", {}).get("dagster", {})

    dagster_group = dagster_metadata.get("group")
    if dagster_group:
        return dagster_group

    dbt_group = dbt_resource_props.get("config", {}).get("group")
    if dbt_group:
        return dbt_group

    return None


def group_from_dbt_resource_props_fallback_to_directory(
    dbt_resource_props: Mapping[str, Any]
) -> Optional[str]:
    """Get the group name for a dbt node.

    Has the same behavior as the default_group_from_dbt_resource_props, except for that, if no group can be determined
    from config or metadata, falls back to using the subdirectory of the models directory that the
    source file is in.

    Args:
        dbt_resource_props (Mapping[str, Any]): A dictionary representing the dbt resource.

    Examples:
        .. code-block:: python

            from dagster_dbt import group_from_dbt_resource_props_fallback_to_directory

            dbt_assets = load_assets_from_dbt_manifest(
                manifest=manifest,
                node_info_to_group_fn=group_from_dbt_resource_props_fallback_to_directory,
            )
    """
    group_name = default_group_from_dbt_resource_props(dbt_resource_props)
    if group_name is not None:
        return group_name

    fqn = dbt_resource_props.get("fqn", [])
    # the first component is the package name, and the last component is the model name
    if len(fqn) < 3:
        return None
    return fqn[1]


def default_freshness_policy_fn(dbt_resource_props: Mapping[str, Any]) -> Optional[FreshnessPolicy]:
    dagster_metadata = dbt_resource_props.get("meta", {}).get("dagster", {})
    freshness_policy_config = dagster_metadata.get("freshness_policy", {})

    freshness_policy = _legacy_freshness_policy_fn(freshness_policy_config)
    if freshness_policy:
        return freshness_policy

    legacy_freshness_policy_config = dbt_resource_props["config"].get(
        "dagster_freshness_policy", {}
    )
    legacy_freshness_policy = _legacy_freshness_policy_fn(legacy_freshness_policy_config)

    if legacy_freshness_policy:
        deprecation_warning(
            "dagster_freshness_policy",
            "0.21.0",
            "Instead, configure a Dagster freshness policy on a dbt model using"
            " +meta.dagster.freshness_policy.",
        )

    return legacy_freshness_policy


def _legacy_freshness_policy_fn(
    freshness_policy_config: Mapping[str, Any]
) -> Optional[FreshnessPolicy]:
    if freshness_policy_config:
        return FreshnessPolicy(
            maximum_lag_minutes=float(freshness_policy_config["maximum_lag_minutes"]),
            cron_schedule=freshness_policy_config.get("cron_schedule"),
            cron_schedule_timezone=freshness_policy_config.get("cron_schedule_timezone"),
        )
    return None


def default_auto_materialize_policy_fn(
    dbt_resource_props: Mapping[str, Any]
) -> Optional[AutoMaterializePolicy]:
    dagster_metadata = dbt_resource_props.get("meta", {}).get("dagster", {})
    auto_materialize_policy_config = dagster_metadata.get("auto_materialize_policy", {})

    auto_materialize_policy = _auto_materialize_policy_fn(auto_materialize_policy_config)
    if auto_materialize_policy:
        return auto_materialize_policy

    legacy_auto_materialize_policy_config = dbt_resource_props["config"].get(
        "dagster_auto_materialize_policy", {}
    )
    legacy_auto_materialize_policy = _auto_materialize_policy_fn(
        legacy_auto_materialize_policy_config
    )

    if legacy_auto_materialize_policy:
        deprecation_warning(
            "dagster_auto_materialize_policy",
            "0.21.0",
            "Instead, configure a Dagster auto-materialize policy on a dbt model using"
            " +meta.dagster.auto_materialize_policy.",
        )

    return legacy_auto_materialize_policy


def _auto_materialize_policy_fn(
    auto_materialize_policy_config: Mapping[str, Any]
) -> Optional[AutoMaterializePolicy]:
    if auto_materialize_policy_config.get("type") == "eager":
        return AutoMaterializePolicy.eager()
    elif auto_materialize_policy_config.get("type") == "lazy":
        return AutoMaterializePolicy.lazy()
    return None


def default_description_fn(dbt_resource_props: Mapping[str, Any], display_raw_sql: bool = True):
    code_block = textwrap.indent(
        dbt_resource_props.get("raw_sql") or dbt_resource_props.get("raw_code", ""), "    "
    )
    description_sections = [
        dbt_resource_props["description"]
        or f"dbt {dbt_resource_props['resource_type']} {dbt_resource_props['name']}",
    ]
    if display_raw_sql:
        description_sections.append(f"#### Raw SQL:\n```\n{code_block}\n```")
    return "\n\n".join(filter(None, description_sections))


def is_generic_test_on_attached_node_from_dbt_resource_props(
    unique_id: str, dbt_resource_props: Mapping[str, Any]
) -> bool:
    attached_node_unique_id = dbt_resource_props.get("attached_node")
    is_generic_test = bool(attached_node_unique_id)

    return is_generic_test and attached_node_unique_id == unique_id


def default_asset_check_fn(
    asset_key: AssetKey,
    unique_id: str,
    dagster_dbt_translator_settings: "DagsterDbtTranslatorSettings",
    dbt_resource_props: Mapping[str, Any],
) -> Optional[AssetCheckSpec]:
    is_generic_test_on_attached_node = is_generic_test_on_attached_node_from_dbt_resource_props(
        unique_id, dbt_resource_props
    )

    if not all(
        [
            dagster_dbt_translator_settings.enable_asset_checks,
            is_generic_test_on_attached_node,
        ]
    ):
        return None

    return AssetCheckSpec(
        name=dbt_resource_props["name"],
        asset=asset_key,
        description=dbt_resource_props["description"],
    )


def default_code_version_fn(dbt_resource_props: Mapping[str, Any]) -> str:
    return hashlib.sha1(
        (dbt_resource_props.get("raw_sql") or dbt_resource_props.get("raw_code", "")).encode(
            "utf-8"
        )
    ).hexdigest()


###################
# DEPENDENCIES
###################


def is_non_asset_node(dbt_resource_props: Mapping[str, Any]):
    # some nodes exist inside the dbt graph but are not assets
    resource_type = dbt_resource_props["resource_type"]
    if resource_type == "metric":
        return True
    if (
        resource_type == "model"
        and dbt_resource_props.get("config", {}).get("materialized") == "ephemeral"
    ):
        return True
    return False


def get_deps(
    dbt_nodes: Mapping[str, Any],
    selected_unique_ids: AbstractSet[str],
    asset_resource_types: List[str],
) -> Mapping[str, FrozenSet[str]]:
    def _valid_parent_node(dbt_resource_props):
        # sources are valid parents, but not assets
        return dbt_resource_props["resource_type"] in asset_resource_types + ["source"]

    asset_deps: Dict[str, Set[str]] = {}
    for unique_id in selected_unique_ids:
        dbt_resource_props = dbt_nodes[unique_id]
        node_resource_type = dbt_resource_props["resource_type"]

        # skip non-assets, such as metrics, tests, and ephemeral models
        if is_non_asset_node(dbt_resource_props) or node_resource_type not in asset_resource_types:
            continue

        asset_deps[unique_id] = set()
        for parent_unique_id in dbt_resource_props.get("depends_on", {}).get("nodes", []):
            parent_node_info = dbt_nodes[parent_unique_id]
            # for metrics or ephemeral dbt models, BFS to find valid parents
            if is_non_asset_node(parent_node_info):
                visited = set()
                replaced_parent_ids = set()
                # make a copy to avoid mutating the actual dictionary
                queue = list(parent_node_info.get("depends_on", {}).get("nodes", []))
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


def get_asset_deps(
    dbt_nodes,
    deps,
    io_manager_key,
    manifest: Optional[Mapping[str, Any]],
    dagster_dbt_translator: "DagsterDbtTranslator",
) -> Tuple[
    Dict[AssetKey, Set[AssetKey]],
    Dict[AssetKey, Tuple[str, In]],
    Dict[AssetKey, Tuple[str, Out]],
    Dict[AssetKey, str],
    Dict[AssetKey, FreshnessPolicy],
    Dict[AssetKey, AutoMaterializePolicy],
    Dict[str, AssetCheckSpec],
    Dict[str, List[str]],
    Dict[str, Dict[str, Any]],
]:
    from .dagster_dbt_translator import DbtManifestWrapper

    asset_deps: Dict[AssetKey, Set[AssetKey]] = {}
    asset_ins: Dict[AssetKey, Tuple[str, In]] = {}
    asset_outs: Dict[AssetKey, Tuple[str, Out]] = {}

    # These dicts could be refactored as a single dict, mapping from output name to arbitrary
    # metadata that we need to store for reference.
    group_names_by_key: Dict[AssetKey, str] = {}
    freshness_policies_by_key: Dict[AssetKey, FreshnessPolicy] = {}
    auto_materialize_policies_by_key: Dict[AssetKey, AutoMaterializePolicy] = {}
    check_specs: List[AssetCheckSpec] = []
    fqns_by_output_name: Dict[str, List[str]] = {}
    metadata_by_output_name: Dict[str, Dict[str, Any]] = {}

    for unique_id, parent_unique_ids in deps.items():
        dbt_resource_props = dbt_nodes[unique_id]

        output_name = output_name_fn(dbt_resource_props)
        fqns_by_output_name[output_name] = dbt_resource_props["fqn"]

        metadata_by_output_name[output_name] = {
            key: dbt_resource_props[key] for key in ["unique_id", "resource_type"]
        }

        asset_key = dagster_dbt_translator.get_asset_key(dbt_resource_props)

        asset_deps[asset_key] = set()

        metadata = merge_dicts(
            dagster_dbt_translator.get_metadata(dbt_resource_props),
            {
                MANIFEST_METADATA_KEY: DbtManifestWrapper(manifest=manifest) if manifest else None,
                DAGSTER_DBT_TRANSLATOR_METADATA_KEY: dagster_dbt_translator,
            },
        )
        asset_outs[asset_key] = (
            output_name,
            Out(
                io_manager_key=io_manager_key,
                description=dagster_dbt_translator.get_description(dbt_resource_props),
                metadata=metadata,
                is_required=False,
                dagster_type=Nothing,
                code_version=default_code_version_fn(dbt_resource_props),
            ),
        )

        group_name = dagster_dbt_translator.get_group_name(dbt_resource_props)
        if group_name is not None:
            group_names_by_key[asset_key] = group_name

        freshness_policy = dagster_dbt_translator.get_freshness_policy(dbt_resource_props)
        if freshness_policy is not None:
            freshness_policies_by_key[asset_key] = freshness_policy

        auto_materialize_policy = dagster_dbt_translator.get_auto_materialize_policy(
            dbt_resource_props
        )
        if auto_materialize_policy is not None:
            auto_materialize_policies_by_key[asset_key] = auto_materialize_policy

        test_unique_ids = []
        if manifest:
            test_unique_ids = [
                child_unique_id
                for child_unique_id in manifest["child_map"][unique_id]
                if child_unique_id.startswith("test")
            ]

            for test_unique_id in test_unique_ids:
                test_resource_props = manifest["nodes"][test_unique_id]
                check_spec = default_asset_check_fn(
                    asset_key, unique_id, dagster_dbt_translator.settings, test_resource_props
                )

                if check_spec:
                    check_specs.append(check_spec)

        for parent_unique_id in parent_unique_ids:
            parent_node_info = dbt_nodes[parent_unique_id]
            parent_asset_key = dagster_dbt_translator.get_asset_key(parent_node_info)

            asset_deps[asset_key].add(parent_asset_key)

            # if this parent is not one of the selected nodes, it's an input
            if parent_unique_id not in deps:
                input_name = input_name_fn(parent_node_info)
                asset_ins[parent_asset_key] = (input_name, In(Nothing))

    check_specs_by_output_name = cast(
        Dict[str, AssetCheckSpec],
        _validate_and_assign_output_names_to_check_specs(check_specs, list(asset_outs.keys())),
    )

    return (
        asset_deps,
        asset_ins,
        asset_outs,
        group_names_by_key,
        freshness_policies_by_key,
        auto_materialize_policies_by_key,
        check_specs_by_output_name,
        fqns_by_output_name,
        metadata_by_output_name,
    )
