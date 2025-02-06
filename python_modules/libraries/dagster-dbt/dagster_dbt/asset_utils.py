import hashlib
import os
import textwrap
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, AbstractSet, Any, Optional  # noqa: UP035

from dagster import (
    AssetCheckKey,
    AssetCheckSpec,
    AssetDep,
    AssetKey,
    AssetsDefinition,
    AssetSelection,
    AssetSpec,
    AutoMaterializePolicy,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    DefaultScheduleStatus,
    FreshnessPolicy,
    RunConfig,
    ScheduleDefinition,
    TableColumn,
    TableSchema,
    _check as check,
    define_asset_job,
)
from dagster._core.definitions.asset_spec import SYSTEM_METADATA_KEY_DAGSTER_TYPE
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataSet,
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
)
from dagster._core.types.dagster_type import Nothing

from dagster_dbt.metadata_set import DbtMetadataSet
from dagster_dbt.utils import (
    ASSET_RESOURCE_TYPES,
    dagster_name_fn,
    get_dbt_resource_props_by_dbt_unique_id_from_manifest,
    select_unique_ids_from_manifest,
)

if TYPE_CHECKING:
    from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DbtManifestWrapper
    from dagster_dbt.dbt_project import DbtProject

DAGSTER_DBT_MANIFEST_METADATA_KEY = "dagster_dbt/manifest"
DAGSTER_DBT_TRANSLATOR_METADATA_KEY = "dagster_dbt/dagster_dbt_translator"
DAGSTER_DBT_SELECT_METADATA_KEY = "dagster_dbt/select"
DAGSTER_DBT_EXCLUDE_METADATA_KEY = "dagster_dbt/exclude"
DAGSTER_DBT_UNIQUE_ID_METADATA_KEY = "dagster_dbt/unique_id"

DUPLICATE_ASSET_KEY_ERROR_MESSAGE = (
    "The following dbt resources are configured with identical Dagster asset keys."
    " Please ensure that each dbt resource generates a unique Dagster asset key."
    " See the reference for configuring Dagster asset keys for your dbt project:"
    " https://docs.dagster.io/integrations/libraries/dbt/reference#customizing-asset-keys."
)


def get_asset_key_for_model(dbt_assets: Sequence[AssetsDefinition], model_name: str) -> AssetKey:
    """Return the corresponding Dagster asset key for a dbt model, seed, or snapshot.

    Args:
        dbt_assets (AssetsDefinition): An AssetsDefinition object produced by @dbt_assets.
        model_name (str): The name of the dbt model, seed, or snapshot.

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
        if value["name"] == model_name and value["resource_type"] in ASSET_RESOURCE_TYPES
    ]

    if len(matching_models) == 0:
        raise KeyError(f"Could not find a dbt model, seed, or snapshot with name: {model_name}")

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
        dagster_name_fn(value): dagster_dbt_translator.get_asset_key(value)
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

        Building an asset selection on a dbt assets definition with an existing selection:

        .. code-block:: python

            from dagster_dbt import dbt_assets, build_dbt_asset_selection

            @dbt_assets(
                manifest=...
                select="bar+",
            )
            def bar_plus_dbt_assets():
                ...

            # Select the dbt assets that are in the intersection of having the tag "foo" and being
            # in the existing selection "bar+".
            bar_plus_and_foo_selection = build_dbt_asset_selection(
                [bar_plus_dbt_assets],
                dbt_select="tag:foo"
            )

            # Furthermore, select all assets downstream (dbt-related or otherwise).
            bar_plus_and_foo_and_downstream_selection = bar_plus_and_foo_selection.downstream()

    """
    manifest, dagster_dbt_translator = get_manifest_and_translator_from_dbt_assets(dbt_assets)
    [dbt_assets_definition] = dbt_assets

    dbt_assets_select = dbt_assets_definition.op.tags[DAGSTER_DBT_SELECT_METADATA_KEY]
    dbt_assets_exclude = dbt_assets_definition.op.tags.get(DAGSTER_DBT_EXCLUDE_METADATA_KEY)

    from dagster_dbt.dbt_manifest_asset_selection import DbtManifestAssetSelection

    return DbtManifestAssetSelection.build(
        manifest=manifest,
        dagster_dbt_translator=dagster_dbt_translator,
        select=dbt_assets_select,
        exclude=dbt_assets_exclude,
    ) & DbtManifestAssetSelection.build(
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
    schedule_name: Optional[str] = None,
    tags: Optional[Mapping[str, str]] = None,
    config: Optional[RunConfig] = None,
    execution_timezone: Optional[str] = None,
    default_status: DefaultScheduleStatus = DefaultScheduleStatus.STOPPED,
) -> ScheduleDefinition:
    """Build a schedule to materialize a specified set of dbt resources from a dbt selection string.

    See https://docs.getdbt.com/reference/node-selection/syntax#how-does-selection-work for
    more information.

    Args:
        job_name (str): The name of the job to materialize the dbt resources.
        cron_schedule (str): The cron schedule to define the schedule.
        dbt_select (str): A dbt selection string to specify a set of dbt resources.
        dbt_exclude (Optional[str]): A dbt selection string to exclude a set of dbt resources.
        schedule_name (Optional[str]): The name of the dbt schedule to create.
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
        name=schedule_name,
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
        default_status=default_status,
    )


def get_manifest_and_translator_from_dbt_assets(
    dbt_assets: Sequence[AssetsDefinition],
) -> tuple[Mapping[str, Any], "DagsterDbtTranslator"]:
    check.invariant(len(dbt_assets) == 1, "Exactly one dbt AssetsDefinition is required")
    dbt_assets_def = dbt_assets[0]
    metadata_by_key = dbt_assets_def.metadata_by_key or {}
    first_asset_key = next(iter(dbt_assets_def.metadata_by_key.keys()))
    first_metadata = metadata_by_key.get(first_asset_key, {})
    manifest_wrapper: Optional[DbtManifestWrapper] = first_metadata.get(
        DAGSTER_DBT_MANIFEST_METADATA_KEY
    )
    if manifest_wrapper is None:
        raise DagsterInvariantViolationError(
            f"Expected to find dbt manifest metadata on asset {first_asset_key.to_user_string()},"
            " but did not. Did you pass in assets that weren't generated by @dbt_assets?"
        )

    dagster_dbt_translator = first_metadata.get(DAGSTER_DBT_TRANSLATOR_METADATA_KEY)
    if dagster_dbt_translator is None:
        raise DagsterInvariantViolationError(
            f"Expected to find dbt translator metadata on asset {first_asset_key.to_user_string()},"
            " but did not. Did you pass in assets that weren't generated by @dbt_assets?"
        )

    return manifest_wrapper.manifest, dagster_dbt_translator


def get_asset_keys_to_resource_props(
    manifest: Mapping[str, Any],
    translator: "DagsterDbtTranslator",
) -> Mapping[AssetKey, Mapping[str, Any]]:
    return {
        translator.get_asset_key(node): node
        for node in manifest["nodes"].values()
        if node["resource_type"] in ASSET_RESOURCE_TYPES
    }


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
    dbt_meta = dbt_resource_props.get("config", {}).get("meta", {}) or dbt_resource_props.get(
        "meta", {}
    )
    dagster_metadata = dbt_meta.get("dagster", {})
    asset_key_config = dagster_metadata.get("asset_key", [])
    if asset_key_config:
        return AssetKey(asset_key_config)

    if dbt_resource_props["resource_type"] == "source":
        components = [dbt_resource_props["source_name"], dbt_resource_props["name"]]
    elif dbt_resource_props.get("version"):
        components = [dbt_resource_props["alias"]]
    else:
        configured_schema = dbt_resource_props["config"].get("schema")
        if configured_schema is not None:
            components = [configured_schema, dbt_resource_props["name"]]
        else:
            components = [dbt_resource_props["name"]]

    return AssetKey(components)


def default_metadata_from_dbt_resource_props(
    dbt_resource_props: Mapping[str, Any],
) -> Mapping[str, Any]:
    column_schema = None
    columns = dbt_resource_props.get("columns", {})
    if len(columns) > 0:
        column_schema = TableSchema(
            columns=[
                TableColumn(
                    name=column_name,
                    type=column_info.get("data_type") or "?",
                    description=column_info.get("description"),
                    tags={tag_name: "" for tag_name in column_info.get("tags", [])},
                )
                for column_name, column_info in columns.items()
            ]
        )

    relation_parts = [
        relation_part
        for relation_part in [
            dbt_resource_props.get("database"),
            dbt_resource_props.get("schema"),
            dbt_resource_props.get("alias"),
        ]
        if relation_part
    ]
    relation_name = ".".join(relation_parts) if relation_parts else None

    materialization_type = dbt_resource_props.get("config", {}).get("materialized")
    return {
        **DbtMetadataSet(materialization_type=materialization_type),
        **TableMetadataSet(
            column_schema=column_schema,
            table_name=relation_name,
        ),
    }


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
    dbt_resource_props: Mapping[str, Any],
) -> Optional[str]:
    """Get the group name for a dbt node.

    Has the same behavior as the default_group_from_dbt_resource_props, except for that, if no group can be determined
    from config or metadata, falls back to using the subdirectory of the models directory that the
    source file is in.

    Args:
        dbt_resource_props (Mapping[str, Any]): A dictionary representing the dbt resource.
    """
    group_name = default_group_from_dbt_resource_props(dbt_resource_props)
    if group_name is not None:
        return group_name

    fqn = dbt_resource_props.get("fqn", [])
    # the first component is the package name, and the last component is the model name
    if len(fqn) < 3:
        return None
    return fqn[1]


def default_owners_from_dbt_resource_props(
    dbt_resource_props: Mapping[str, Any],
) -> Optional[Sequence[str]]:
    dagster_metadata = dbt_resource_props.get("meta", {}).get("dagster", {})
    owners_config = dagster_metadata.get("owners")

    if owners_config:
        return owners_config

    owner: Optional[str] = (dbt_resource_props.get("group") or {}).get("owner", {}).get("email")

    if not owner:
        return None

    return [owner]


def default_freshness_policy_fn(dbt_resource_props: Mapping[str, Any]) -> Optional[FreshnessPolicy]:
    dagster_metadata = dbt_resource_props.get("meta", {}).get("dagster", {})
    freshness_policy_config = dagster_metadata.get("freshness_policy", {})

    freshness_policy = (
        FreshnessPolicy(
            maximum_lag_minutes=float(freshness_policy_config["maximum_lag_minutes"]),
            cron_schedule=freshness_policy_config.get("cron_schedule"),
            cron_schedule_timezone=freshness_policy_config.get("cron_schedule_timezone"),
        )
        if freshness_policy_config
        else None
    )

    return freshness_policy


def default_auto_materialize_policy_fn(
    dbt_resource_props: Mapping[str, Any],
) -> Optional[AutoMaterializePolicy]:
    dagster_metadata = dbt_resource_props.get("meta", {}).get("dagster", {})
    auto_materialize_policy_config = dagster_metadata.get("auto_materialize_policy", {})

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
        description_sections.append(f"#### Raw SQL:\n```sql\n{code_block}\n```")
    return "\n\n".join(filter(None, description_sections))


def default_asset_check_fn(
    manifest: Mapping[str, Any],
    dbt_nodes: Mapping[str, Any],
    dagster_dbt_translator: "DagsterDbtTranslator",
    asset_key: AssetKey,
    test_unique_id: str,
) -> Optional[AssetCheckSpec]:
    if not dagster_dbt_translator.settings.enable_asset_checks:
        return None

    test_resource_props = dbt_nodes[test_unique_id]
    parent_unique_ids: set[str] = set(manifest["parent_map"].get(test_unique_id, []))

    asset_check_key = get_asset_check_key_for_test(
        manifest=manifest,
        dagster_dbt_translator=dagster_dbt_translator,
        test_unique_id=test_unique_id,
    )

    if not (asset_check_key and asset_check_key.asset_key == asset_key):
        return None

    additional_deps = {
        dagster_dbt_translator.get_asset_key(dbt_nodes[parent_id])
        for parent_id in parent_unique_ids
    }
    additional_deps.discard(asset_key)

    return AssetCheckSpec(
        name=test_resource_props["name"],
        asset=asset_key,
        description=test_resource_props.get("meta", {}).get("description"),
        additional_deps=additional_deps,
        metadata={DAGSTER_DBT_UNIQUE_ID_METADATA_KEY: test_unique_id},
    )


def default_code_version_fn(dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
    code: Optional[str] = dbt_resource_props.get("raw_sql") or dbt_resource_props.get("raw_code")
    if code:
        return hashlib.sha1(code.encode("utf-8")).hexdigest()

    return dbt_resource_props.get("checksum", {}).get("checksum")


def _attach_sql_model_code_reference(
    existing_metadata: Mapping[str, Any],
    dbt_resource_props: Mapping[str, Any],
    project: "DbtProject",
) -> Mapping[str, Any]:
    """Pulls the SQL model location for a dbt resource and attaches it as a code reference to the
    existing metadata.
    """
    existing_references_meta = CodeReferencesMetadataSet.extract(existing_metadata)
    references = (
        existing_references_meta.code_references.code_references
        if existing_references_meta.code_references
        else []
    )

    if "original_file_path" not in dbt_resource_props:
        raise DagsterInvalidDefinitionError(
            "Cannot attach SQL model code reference because 'original_file_path' is not present"
            " in the dbt resource properties."
        )

    # attempt to get root_path, which is removed from manifests in newer dbt versions
    relative_path = Path(dbt_resource_props["original_file_path"])
    abs_path = project.project_dir.joinpath(relative_path).resolve()

    return {
        **existing_metadata,
        **CodeReferencesMetadataSet(
            code_references=CodeReferencesMetadataValue(
                code_references=[
                    *references,
                    LocalFileCodeReference(file_path=os.fspath(abs_path)),
                ],
            )
        ),
    }


###################
# DEPENDENCIES
###################


def is_non_asset_node(dbt_resource_props: Mapping[str, Any]):
    # some nodes exist inside the dbt graph but are not assets
    resource_type = dbt_resource_props["resource_type"]

    return any(
        [
            resource_type == "metric",
            resource_type == "semantic_model",
            resource_type == "saved_query",
            resource_type == "model"
            and dbt_resource_props.get("config", {}).get("materialized") == "ephemeral",
        ]
    )


def is_valid_upstream_node(dbt_resource_props: Mapping[str, Any]) -> bool:
    # sources are valid parents, but not assets
    return dbt_resource_props["resource_type"] in ASSET_RESOURCE_TYPES + ["source"]


def get_upstream_unique_ids(
    dbt_nodes: Mapping[str, Any], dbt_resource_props: Mapping[str, Any]
) -> AbstractSet[str]:
    upstreams = set()
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
                elif is_valid_upstream_node(candidate_parent_info):
                    replaced_parent_ids.add(candidate_parent_id)

            upstreams |= replaced_parent_ids
        # ignore nodes which are not assets / sources
        elif is_valid_upstream_node(parent_node_info):
            upstreams.add(parent_unique_id)

    return upstreams


def get_asset_spec(
    translator: "DagsterDbtTranslator",
    manifest: Mapping[str, Any],
    dbt_nodes: Mapping[str, Any],
    group_props: Mapping[str, Any],
    project: Optional["DbtProject"],
    resource_props: Mapping[str, Any],
) -> AssetSpec:
    """Returns an AssetSpec representing a specific dbt resource. In the future, this will be a method directly on
    the DagsterDbtTranslator.
    """
    from dagster_dbt.dagster_dbt_translator import DbtManifestWrapper

    # calculate the dependencies for the asset
    upstream_ids = get_upstream_unique_ids(dbt_nodes, resource_props)
    deps = [
        AssetDep(
            asset=translator.get_asset_key(dbt_nodes[upstream_id]),
            partition_mapping=translator.get_partition_mapping(
                resource_props, dbt_nodes[upstream_id]
            ),
        )
        for upstream_id in upstream_ids
    ]
    self_partition_mapping = translator.get_partition_mapping(resource_props, resource_props)
    if self_partition_mapping and has_self_dependency(resource_props):
        deps.append(
            AssetDep(
                asset=translator.get_asset_key(resource_props),
                partition_mapping=self_partition_mapping,
            )
        )

    resource_group_props = group_props.get(resource_props.get("group") or "")
    spec = AssetSpec(
        key=translator.get_asset_key(resource_props),
        deps=deps,
        description=translator.get_description(resource_props),
        metadata=translator.get_metadata(resource_props),
        skippable=True,
        group_name=translator.get_group_name(resource_props),
        code_version=translator.get_code_version(resource_props),
        automation_condition=translator.get_automation_condition(resource_props),
        freshness_policy=translator.get_freshness_policy(resource_props),
        owners=translator.get_owners(
            {
                **resource_props,
                # this overrides the group key in resource_props, which is bad as
                # this key is not always empty and this dictionary generally differs
                # in structure from other inputs, but this is necessary for backcompat
                **({"group": resource_group_props} if resource_group_props else {}),
            }
        ),
        tags=translator.get_tags(resource_props),
        kinds={"dbt", manifest.get("metadata", {}).get("adapter_type", "dbt")},
        partitions_def=translator.get_partitions_def(resource_props),
    )

    # add integration-specific metadata to the spec
    spec = spec.merge_attributes(
        metadata={
            DAGSTER_DBT_MANIFEST_METADATA_KEY: DbtManifestWrapper(manifest=manifest),
            DAGSTER_DBT_TRANSLATOR_METADATA_KEY: translator,
            DAGSTER_DBT_UNIQUE_ID_METADATA_KEY: resource_props["unique_id"],
        }
    )
    if translator.settings.enable_code_references:
        if not project:
            raise DagsterInvalidDefinitionError(
                "enable_code_references requires a DbtProject to be supplied"
                " to the @dbt_assets decorator."
            )

        spec = spec.replace_attributes(
            metadata=_attach_sql_model_code_reference(
                existing_metadata=spec.metadata,
                dbt_resource_props=resource_props,
                project=project,
            )
        )
    return spec


def build_dbt_specs(
    *,
    translator: "DagsterDbtTranslator",
    manifest: Mapping[str, Any],
    select: str,
    exclude: str,
    io_manager_key: Optional[str],
    project: Optional["DbtProject"],
) -> tuple[Sequence[AssetSpec], Sequence[AssetCheckSpec]]:
    dbt_nodes = get_dbt_resource_props_by_dbt_unique_id_from_manifest(manifest)
    group_props = {group["name"]: group for group in manifest.get("groups", {}).values()}

    selected_unique_ids = select_unique_ids_from_manifest(
        select=select, exclude=exclude, manifest_json=manifest
    )

    specs: list[AssetSpec] = []
    check_specs: list[AssetCheckSpec] = []
    key_by_unique_id: dict[str, AssetKey] = {}
    for unique_id in selected_unique_ids:
        resource_props = dbt_nodes[unique_id]
        resource_type = resource_props["resource_type"]

        # skip non-assets, such as semantic models, metrics, tests, and ephemeral models
        if is_non_asset_node(resource_props) or resource_type not in ASSET_RESOURCE_TYPES:
            continue

        # get the spec for the given node
        spec = get_asset_spec(translator, manifest, dbt_nodes, group_props, project, resource_props)
        key_by_unique_id[unique_id] = spec.key

        # add the io manager key and set the dagster type to Nothing
        if io_manager_key is not None:
            spec = spec.with_io_manager_key(io_manager_key)
            spec = spec.merge_attributes(metadata={SYSTEM_METADATA_KEY_DAGSTER_TYPE: Nothing})

        specs.append(spec)

        # add check specs associated with the asset
        for child_unique_id in manifest["child_map"][unique_id]:
            if not child_unique_id.startswith("test"):
                continue

            check_spec = default_asset_check_fn(
                manifest, dbt_nodes, translator, spec.key, child_unique_id
            )
            if check_spec:
                check_specs.append(check_spec)

        # update the keys_by_unqiue_id dictionary to include keys created for upstream
        # assets. note that this step may need to change once the translator is updated
        # to no longer rely on `get_asset_key` as a standalone method
        for upstream_id in get_upstream_unique_ids(dbt_nodes, resource_props):
            key_by_unique_id[upstream_id] = translator.get_asset_key(dbt_nodes[upstream_id])

    _validate_asset_keys(translator, dbt_nodes, key_by_unique_id)
    return specs, check_specs


def _validate_asset_keys(
    translator: "DagsterDbtTranslator",
    dbt_nodes: Mapping[str, Any],
    key_by_unique_id: Mapping[str, AssetKey],
) -> None:
    unique_ids_by_key = defaultdict(set)
    for unique_id, key in key_by_unique_id.items():
        unique_ids_by_key[key].add(unique_id)

    error_messages = []
    for key, unique_ids in unique_ids_by_key.items():
        if len(unique_ids) == 1:
            continue
        if translator.settings.enable_duplicate_source_asset_keys:
            resource_types = {dbt_nodes[unique_id]["resource_type"] for unique_id in unique_ids}
            if resource_types == {"source"}:
                continue
        formatted_ids = [
            f"  - `{id}` ({dbt_nodes[id]['original_file_path']})" for id in sorted(unique_ids)
        ]
        error_messages.append(
            "\n".join(
                [
                    f"The following dbt resources have the asset key `{key.path}`:",
                    *formatted_ids,
                ]
            )
        )

    if error_messages:
        raise DagsterInvalidDefinitionError(
            "\n\n".join([DUPLICATE_ASSET_KEY_ERROR_MESSAGE, *error_messages])
        )


def has_self_dependency(dbt_resource_props: Mapping[str, Any]) -> bool:
    dagster_metadata = dbt_resource_props.get("meta", {}).get("dagster", {})
    has_self_dependency = dagster_metadata.get("has_self_dependency", False)

    return has_self_dependency


def get_asset_check_key_for_test(
    manifest: Mapping[str, Any],
    dagster_dbt_translator: "DagsterDbtTranslator",
    test_unique_id: str,
) -> Optional[AssetCheckKey]:
    if not test_unique_id.startswith("test"):
        return None

    test_resource_props = manifest["nodes"][test_unique_id]
    upstream_unique_ids: AbstractSet[str] = set(test_resource_props["depends_on"]["nodes"])

    # If the test is generic, it will have an attached node that we can use.
    attached_node_unique_id = test_resource_props.get("attached_node")

    # If the test is singular, infer the attached node from the upstream nodes.
    if len(upstream_unique_ids) == 1:
        [attached_node_unique_id] = upstream_unique_ids

    # If the test is singular, but has multiple dependencies, infer the attached node from
    # from the dbt meta.
    attached_node_ref = (
        (
            test_resource_props.get("config", {}).get("meta", {})
            or test_resource_props.get("meta", {})
        )
        .get("dagster", {})
        .get("ref", {})
    )

    # Attempt to find the attached node from the ref.
    if attached_node_ref:
        ref_name, ref_package, ref_version = (
            attached_node_ref["name"],
            attached_node_ref.get("package"),
            attached_node_ref.get("version"),
        )

        project_name = manifest["metadata"]["project_name"]
        if not ref_package:
            ref_package = project_name

        unique_id_by_ref: Mapping[tuple[str, str, Optional[str]], str] = {
            (
                dbt_resource_props["name"],
                dbt_resource_props["package_name"],
                dbt_resource_props.get("version"),
            ): unique_id
            for unique_id, dbt_resource_props in manifest["nodes"].items()
        }

        attached_node_unique_id = unique_id_by_ref.get((ref_name, ref_package, ref_version))

    if not attached_node_unique_id:
        return None

    return AssetCheckKey(
        name=test_resource_props["name"],
        asset_key=dagster_dbt_translator.get_asset_key(
            manifest["nodes"].get(attached_node_unique_id)
            or manifest["sources"].get(attached_node_unique_id)
        ),
    )
