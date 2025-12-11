import hashlib
import os
import shutil
import tempfile
import textwrap
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, AbstractSet, Annotated, Any, Final, Optional, Union  # noqa: UP035

import yaml
from dagster import (
    AssetCheckKey,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    AssetsDefinition,
    AssetSelection,
    AssetSpec,
    AutoMaterializePolicy,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    DefaultScheduleStatus,
    OpExecutionContext,
    RunConfig,
    ScheduleDefinition,
    TableColumn,
    TableSchema,
    _check as check,
    define_asset_job,
    get_dagster_logger,
)
from dagster._core.definitions.assets.definition.asset_spec import SYSTEM_METADATA_KEY_DAGSTER_TYPE
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._core.errors import DagsterInvalidPropertyError
from dagster._core.types.dagster_type import Nothing
from dagster._record import ImportFrom, record
from dagster_shared.record import replace

from dagster_dbt.dbt_project import DbtProject
from dagster_dbt.metadata_set import DbtMetadataSet
from dagster_dbt.utils import ASSET_RESOURCE_TYPES, dagster_name_fn, select_unique_ids

if TYPE_CHECKING:
    from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DbtManifestWrapper

DAGSTER_DBT_MANIFEST_METADATA_KEY = "dagster_dbt/manifest"
DAGSTER_DBT_TRANSLATOR_METADATA_KEY = "dagster_dbt/dagster_dbt_translator"
DAGSTER_DBT_PROJECT_METADATA_KEY = "dagster_dbt/project"
DAGSTER_DBT_SELECT_METADATA_KEY = "dagster_dbt/select"
DAGSTER_DBT_EXCLUDE_METADATA_KEY = "dagster_dbt/exclude"
DAGSTER_DBT_SELECTOR_METADATA_KEY = "dagster_dbt/selector"
DAGSTER_DBT_UNIQUE_ID_METADATA_KEY = "dagster_dbt/unique_id"

DBT_DEFAULT_SELECT = "fqn:*"
DBT_DEFAULT_EXCLUDE = ""
DBT_DEFAULT_SELECTOR = ""

DBT_INDIRECT_SELECTION_ENV: Final[str] = "DBT_INDIRECT_SELECTION"
DBT_EMPTY_INDIRECT_SELECTION: Final[str] = "empty"

# Threshold for switching to selector file to avoid CLI argument length limits
# https://github.com/dagster-io/dagster/issues/16997
_SELECTION_ARGS_THRESHOLD: Final[int] = 200

DUPLICATE_ASSET_KEY_ERROR_MESSAGE = (
    "The following dbt resources are configured with identical Dagster asset keys."
    " Please ensure that each dbt resource generates a unique Dagster asset key."
    " See the reference for configuring Dagster asset keys for your dbt project:"
    " https://docs.dagster.io/integrations/libraries/dbt/reference#customizing-asset-keys."
)

logger = get_dagster_logger()


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

    manifest, dagster_dbt_translator, dbt_project = get_manifest_and_translator_from_dbt_assets(
        dbt_assets
    )

    matching_model_ids = [
        unique_id
        for unique_id, value in manifest["nodes"].items()
        if value["name"] == model_name and value["resource_type"] in ASSET_RESOURCE_TYPES
    ]

    if len(matching_model_ids) == 0:
        raise KeyError(f"Could not find a dbt model, seed, or snapshot with name: {model_name}")

    return dagster_dbt_translator.get_asset_spec(
        manifest,
        next(iter(matching_model_ids)),
        dbt_project,
    ).key


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

    manifest, dagster_dbt_translator, dbt_project = get_manifest_and_translator_from_dbt_assets(
        dbt_assets
    )

    matching = {
        unique_id: value
        for unique_id, value in manifest["sources"].items()
        if value["source_name"] == source_name
    }

    if len(matching) == 0:
        raise KeyError(f"Could not find a dbt source with name: {source_name}")

    return {
        dagster_name_fn(value): dagster_dbt_translator.get_asset_spec(
            manifest, unique_id, dbt_project
        ).key
        for unique_id, value in matching.items()
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
    dbt_select: str = DBT_DEFAULT_SELECT,
    dbt_exclude: Optional[str] = DBT_DEFAULT_EXCLUDE,
    dbt_selector: Optional[str] = DBT_DEFAULT_SELECTOR,
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
    manifest, dagster_dbt_translator, dbt_project = get_manifest_and_translator_from_dbt_assets(
        dbt_assets
    )
    [dbt_assets_definition] = dbt_assets

    dbt_assets_select = dbt_assets_definition.op.tags[DAGSTER_DBT_SELECT_METADATA_KEY]
    dbt_assets_exclude = dbt_assets_definition.op.tags.get(
        DAGSTER_DBT_EXCLUDE_METADATA_KEY, DBT_DEFAULT_EXCLUDE
    )
    dbt_assets_selector = dbt_assets_definition.op.tags.get(
        DAGSTER_DBT_SELECTOR_METADATA_KEY, DBT_DEFAULT_SELECTOR
    )

    from dagster_dbt.dbt_manifest_asset_selection import DbtManifestAssetSelection

    return DbtManifestAssetSelection.build(
        manifest=manifest,
        dagster_dbt_translator=dagster_dbt_translator,
        select=dbt_assets_select,
        exclude=dbt_assets_exclude,
        selector=dbt_assets_selector,
        project=dbt_project,
    ) & DbtManifestAssetSelection.build(
        manifest=manifest,
        dagster_dbt_translator=dagster_dbt_translator,
        select=dbt_select,
        exclude=dbt_exclude or DBT_DEFAULT_EXCLUDE,
        selector=dbt_selector or DBT_DEFAULT_SELECTOR,
        project=dbt_project,
    )


def build_schedule_from_dbt_selection(
    dbt_assets: Sequence[AssetsDefinition],
    job_name: str,
    cron_schedule: str,
    dbt_select: str = DBT_DEFAULT_SELECT,
    dbt_exclude: Optional[str] = DBT_DEFAULT_EXCLUDE,
    dbt_selector: str = DBT_DEFAULT_SELECTOR,
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
        dbt_selector (str): A dbt selector to select resources to materialize.
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
                dbt_exclude=dbt_exclude or DBT_DEFAULT_EXCLUDE,
                dbt_selector=dbt_selector,
            ),
            config=config,
            tags=tags,
        ),
        execution_timezone=execution_timezone,
        default_status=default_status,
    )


def get_manifest_and_translator_from_dbt_assets(
    dbt_assets: Sequence[AssetsDefinition],
) -> tuple[Mapping[str, Any], "DagsterDbtTranslator", Optional[DbtProject]]:
    check.invariant(len(dbt_assets) == 1, "Exactly one dbt AssetsDefinition is required")
    dbt_assets_def = dbt_assets[0]
    metadata_by_key = dbt_assets_def.metadata_by_key or {}
    first_asset_key = next(iter(dbt_assets_def.metadata_by_key.keys()))
    first_metadata = metadata_by_key.get(first_asset_key, {})
    manifest_wrapper: Optional[DbtManifestWrapper] = first_metadata.get(
        DAGSTER_DBT_MANIFEST_METADATA_KEY
    )
    project = first_metadata.get(DAGSTER_DBT_PROJECT_METADATA_KEY)
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

    return manifest_wrapper.manifest, dagster_dbt_translator, project


def get_asset_keys_to_resource_props(
    manifest: Mapping[str, Any],
    translator: "DagsterDbtTranslator",
) -> Mapping[AssetKey, Mapping[str, Any]]:
    return {
        translator.get_asset_key(node): node
        for node in manifest["nodes"].values()
        if node["resource_type"] in ASSET_RESOURCE_TYPES
    }


@record
class DbtCliInvocationPartialParams:
    manifest: Mapping[str, Any]
    dagster_dbt_translator: Annotated[
        "DagsterDbtTranslator", ImportFrom("dagster_dbt.dagster_dbt_translator")
    ]
    selection_args: Sequence[str]
    indirect_selection: Optional[str]
    dbt_project: Optional[DbtProject]


def get_updated_cli_invocation_params_for_context(
    context: Optional[Union[OpExecutionContext, AssetExecutionContext]],
    manifest: Mapping[str, Any],
    dagster_dbt_translator: "DagsterDbtTranslator",
) -> DbtCliInvocationPartialParams:
    try:
        assets_def = context.assets_def if context else None
    except DagsterInvalidPropertyError:
        # If assets_def is None in an OpExecutionContext, we raise a DagsterInvalidPropertyError,
        # but we don't want to raise the error here.
        assets_def = None

    selection_args: list[str] = []
    indirect_selection = os.getenv(DBT_INDIRECT_SELECTION_ENV, None)
    dbt_project = None
    if context and assets_def is not None:
        manifest, dagster_dbt_translator, dbt_project = get_manifest_and_translator_from_dbt_assets(
            [assets_def]
        )

        # Get project_dir from dbt_project if available
        project_dir = Path(dbt_project.project_dir) if dbt_project else None
        target_project = dbt_project

        selection_args, indirect_selection_override = get_subset_selection_for_context(
            context=context,
            manifest=manifest,
            select=context.op.tags.get(DAGSTER_DBT_SELECT_METADATA_KEY),
            exclude=context.op.tags.get(DAGSTER_DBT_EXCLUDE_METADATA_KEY),
            selector=context.op.tags.get(DAGSTER_DBT_SELECTOR_METADATA_KEY),
            dagster_dbt_translator=dagster_dbt_translator,
            current_dbt_indirect_selection_env=indirect_selection,
        )
        if (
            selection_args[0] == "--select"
            and project_dir
            and len(resources := selection_args[1].split(" ")) > _SELECTION_ARGS_THRESHOLD
        ):
            temp_project_dir = tempfile.mkdtemp()
            shutil.copytree(project_dir, temp_project_dir, dirs_exist_ok=True)
            selectors_path = Path(temp_project_dir) / "selectors.yml"

            # Delete any existing selectors, we need to create our own
            if selectors_path.exists():
                selectors_path.unlink()

            selector_name = f"dagster_run_{context.run_id}"
            temp_selectors = {
                "selectors": [
                    {
                        "name": selector_name,
                        "definition": {"union": list(resources)},
                    }
                ]
            }
            selectors_path.write_text(yaml.safe_dump(temp_selectors))
            logger.info(
                f"DBT selection of {len(resources)} resources exceeds threshold of {_SELECTION_ARGS_THRESHOLD}. "
                "This may exceed system argument length limits. "
                f"Executing materialization against temporary copy of DBT project at {temp_project_dir} with ephemeral selector."
            )
            selection_args = ["--selector", selector_name]
            target_project = replace(dbt_project, project_dir=Path(temp_project_dir))

        indirect_selection = (
            indirect_selection_override if indirect_selection_override else indirect_selection
        )
    else:
        target_project = dbt_project

    return DbtCliInvocationPartialParams(
        manifest=manifest,
        dagster_dbt_translator=dagster_dbt_translator,
        selection_args=selection_args,
        indirect_selection=indirect_selection,
        dbt_project=target_project,
    )


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
            dbt_resource_props.get("name")
            if dbt_resource_props.get("resource_type") == "source"
            else None,
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

    owner: Optional[Union[str, Sequence[str]]] = (
        (dbt_resource_props.get("group") or {}).get("owner", {}).get("email")
    )

    if not owner:
        return None

    return [owner] if isinstance(owner, str) else owner


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
        dbt_resource_props.get("description")
        or f"dbt {dbt_resource_props['resource_type']} {dbt_resource_props['name']}",
    ]
    if display_raw_sql:
        description_sections.append(f"#### Raw SQL:\n```sql\n{code_block}\n```")
    return "\n\n".join(filter(None, description_sections))


def default_asset_check_fn(
    manifest: Mapping[str, Any],
    dagster_dbt_translator: "DagsterDbtTranslator",
    asset_key: AssetKey,
    test_unique_id: str,
    project: Optional[DbtProject],
) -> Optional[AssetCheckSpec]:
    if not dagster_dbt_translator.settings.enable_asset_checks:
        return None

    test_resource_props = get_node(manifest, test_unique_id)
    parent_unique_ids: set[str] = set(manifest["parent_map"].get(test_unique_id, []))

    asset_check_key = get_asset_check_key_for_test(
        manifest=manifest,
        dagster_dbt_translator=dagster_dbt_translator,
        test_unique_id=test_unique_id,
        project=project,
    )

    if not (asset_check_key and asset_check_key.asset_key == asset_key):
        return None

    additional_deps = {
        dagster_dbt_translator.get_asset_spec(manifest, parent_id, project).key
        for parent_id in parent_unique_ids
    }
    additional_deps.discard(asset_key)

    severity = test_resource_props.get("config", {}).get("severity", "error")
    blocking = severity.lower() == "error"

    return AssetCheckSpec(
        name=test_resource_props["name"],
        asset=asset_key,
        description=test_resource_props.get("meta", {}).get("description"),
        additional_deps=additional_deps,
        metadata={DAGSTER_DBT_UNIQUE_ID_METADATA_KEY: test_unique_id},
        blocking=blocking,
    )


def default_code_version_fn(dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
    code: Optional[str] = dbt_resource_props.get("raw_sql") or dbt_resource_props.get("raw_code")
    if code:
        return hashlib.sha1(code.encode("utf-8")).hexdigest()

    return dbt_resource_props.get("checksum", {}).get("checksum")


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
    manifest: Mapping[str, Any],
    dbt_resource_props: Mapping[str, Any],
) -> AbstractSet[str]:
    upstreams = set()
    for parent_unique_id in dbt_resource_props.get("depends_on", {}).get("nodes", []):
        parent_node_info = get_node(manifest, parent_unique_id)
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

                candidate_parent_info = get_node(manifest, candidate_parent_id)
                if is_non_asset_node(candidate_parent_info):
                    queue.extend(candidate_parent_info.get("depends_on", {}).get("nodes", []))
                elif is_valid_upstream_node(candidate_parent_info):
                    replaced_parent_ids.add(candidate_parent_id)

            upstreams |= replaced_parent_ids
        # ignore nodes which are not assets / sources
        elif is_valid_upstream_node(parent_node_info):
            upstreams.add(parent_unique_id)

    return upstreams


def _build_child_map(manifest: Mapping[str, Any]) -> Mapping[str, AbstractSet[str]]:
    """Manifests produced by early versions of dbt Fusion do not contain a child map, so we need to build it manually."""
    if manifest.get("child_map"):
        return manifest["child_map"]

    child_map = defaultdict(set)
    for unique_id, node in manifest["nodes"].items():
        for upstream_unique_id in get_upstream_unique_ids(manifest, node):
            child_map[upstream_unique_id].add(unique_id)
    return child_map


def build_dbt_specs(
    *,
    translator: "DagsterDbtTranslator",
    manifest: Mapping[str, Any],
    select: str,
    exclude: str,
    selector: str,
    io_manager_key: Optional[str],
    project: Optional[DbtProject],
) -> tuple[Sequence[AssetSpec], Sequence[AssetCheckSpec]]:
    selected_unique_ids = select_unique_ids(
        select=select, exclude=exclude, selector=selector, project=project, manifest_json=manifest
    )

    specs: list[AssetSpec] = []
    check_specs: dict[str, AssetCheckSpec] = {}
    key_by_unique_id: dict[str, AssetKey] = {}

    child_map = _build_child_map(manifest)
    for unique_id in selected_unique_ids:
        resource_props = get_node(manifest, unique_id)
        resource_type = resource_props["resource_type"]

        # skip non-assets, such as semantic models, metrics, tests, and ephemeral models
        if is_non_asset_node(resource_props) or resource_type not in ASSET_RESOURCE_TYPES:
            continue

        # get the spec for the given node
        spec = translator.get_asset_spec(
            manifest,
            unique_id,
            project,
        )
        key_by_unique_id[unique_id] = spec.key

        # add the io manager key and set the dagster type to Nothing
        if io_manager_key is not None:
            spec = spec.with_io_manager_key(io_manager_key)
            spec = spec.merge_attributes(metadata={SYSTEM_METADATA_KEY_DAGSTER_TYPE: Nothing})

        specs.append(spec)

        # add check specs associated with the asset
        for child_unique_id in child_map.get(unique_id, []):
            if child_unique_id not in selected_unique_ids or not child_unique_id.startswith("test"):
                continue
            check_spec = translator.get_asset_check_spec(
                asset_spec=spec,
                manifest=manifest,
                unique_id=child_unique_id,
                project=project,
            )

            if check_spec:
                check_specs[check_spec.get_python_identifier()] = check_spec

        # update the keys_by_unqiue_id dictionary to include keys created for upstream
        # assets. note that this step may need to change once the translator is updated
        # to no longer rely on `get_asset_key` as a standalone method
        for upstream_id in get_upstream_unique_ids(manifest, resource_props):
            spec = translator.get_asset_spec(manifest, upstream_id, project)
            key_by_unique_id[upstream_id] = spec.key
            if (
                upstream_id.startswith("source")
                and translator.settings.enable_source_tests_as_checks
            ):
                for child_unique_id in child_map.get(upstream_id, []):
                    if not child_unique_id.startswith("test"):
                        continue
                    check_spec = translator.get_asset_check_spec(
                        asset_spec=spec,
                        manifest=manifest,
                        unique_id=child_unique_id,
                        project=project,
                    )
                    if check_spec:
                        check_specs[check_spec.get_python_identifier()] = check_spec

    _validate_asset_keys(translator, manifest, key_by_unique_id)
    return specs, list(check_specs.values())


def _validate_asset_keys(
    translator: "DagsterDbtTranslator",
    manifest: Mapping[str, Any],
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
            resource_types = {
                get_node(manifest, unique_id)["resource_type"] for unique_id in unique_ids
            }
            if resource_types == {"source"}:
                continue
        formatted_ids = [
            f"  - `{id}` ({get_node(manifest, id)['original_file_path']})"
            for id in sorted(unique_ids)
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
    project: Optional[DbtProject],
) -> Optional[AssetCheckKey]:
    if not test_unique_id.startswith("test"):
        return None

    test_resource_props = get_node(manifest, test_unique_id)
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

        project_name = manifest.get("metadata", {})["project_name"]
        if not ref_package:
            ref_package = project_name

        attached_node_unique_id = None
        for unique_id, dbt_resource_props in manifest["nodes"].items():
            if (ref_name, ref_package, ref_version) == (
                dbt_resource_props["name"],
                dbt_resource_props["package_name"],
                dbt_resource_props.get("version"),
            ):
                attached_node_unique_id = unique_id
                break

    if not attached_node_unique_id:
        return None

    return AssetCheckKey(
        name=test_resource_props["name"],
        asset_key=dagster_dbt_translator.get_asset_spec(
            manifest,
            attached_node_unique_id,
            project,
        ).key,
    )


def get_checks_on_sources_upstream_of_selected_assets(
    assets_def: AssetsDefinition, selected_asset_keys: AbstractSet[AssetKey]
) -> AbstractSet[AssetCheckKey]:
    upstream_source_keys = assets_def.get_upstream_input_keys(frozenset(selected_asset_keys))
    return assets_def.get_checks_targeting_keys(frozenset(upstream_source_keys))


def get_subset_selection_for_context(
    context: Union[OpExecutionContext, AssetExecutionContext],
    manifest: Mapping[str, Any],
    select: Optional[str],
    exclude: Optional[str],
    selector: Optional[str],
    dagster_dbt_translator: "DagsterDbtTranslator",
    current_dbt_indirect_selection_env: Optional[str],
) -> tuple[list[str], Optional[str]]:
    """Generate a dbt selection string and DBT_INDIRECT_SELECTION setting to execute the selected
    resources in a subsetted execution context.

    See https://docs.getdbt.com/reference/node-selection/syntax#how-does-selection-work.

    Args:
        context (Union[OpExecutionContext, AssetExecutionContext]): The execution context for the current execution step.
        manifest (Mapping[str, Any]): The dbt manifest blob.
        select (Optional[str]): A dbt selection string to select resources to materialize.
        exclude (Optional[str]): A dbt selection string to exclude resources from materializing.
        selector (Optional[str]): A dbt selector to select resources to materialize.
        dagster_dbt_translator (DagsterDbtTranslator): The translator to link dbt nodes to Dagster
            assets.
        current_dbt_indirect_selection_env (Optional[str]): The user's value for the DBT_INDIRECT_SELECTION
            environment variable.


    Returns:
        List[str]: dbt CLI arguments to materialize the selected resources in a
            subsetted execution context.

            If the current execution context is not performing a subsetted execution,
            return CLI arguments composed of the inputed selection and exclusion arguments.
        Optional[str]: A value for the DBT_INDIRECT_SELECTION environment variable. If None, then
            the environment variable is not set and will either use dbt's default (eager) or the
            user's setting.
    """
    default_dbt_selection = []
    if select:
        default_dbt_selection += ["--select", select]
    if exclude:
        default_dbt_selection += ["--exclude", exclude]
    if selector:
        default_dbt_selection += ["--selector", selector]

    assets_def = context.assets_def
    is_asset_subset = assets_def.keys_by_output_name != assets_def.node_keys_by_output_name
    is_checks_subset = (
        assets_def.check_specs_by_output_name != assets_def.node_check_specs_by_output_name
    )

    # It's nice to use the default dbt selection arguments when not subsetting for readability. We
    # also use dbt indirect selection to avoid hitting cli arg length limits.
    # https://github.com/dagster-io/dagster/issues/16997#issuecomment-1832443279
    # A biproduct is that we'll run singular dbt tests (not currently modeled as asset checks) in
    # cases when we can use indirection selection, an not when we need to turn it off.
    if not (is_asset_subset or is_checks_subset):
        logger.info(
            "A dbt subsetted execution is not being performed. Using the default dbt selection"
            f" arguments `{default_dbt_selection}`."
        )
        # default eager indirect selection. This means we'll also run any singular tests (which
        # aren't modeled as asset checks currently).
        return default_dbt_selection, None

    # Explicitly select a dbt resource by its path. Selecting a resource by path is more terse
    # than selecting it by its fully qualified name.
    # https://docs.getdbt.com/reference/node-selection/methods#the-path-method
    selected_asset_resources = get_dbt_resource_names_for_asset_keys(
        dagster_dbt_translator, manifest, assets_def, context.selected_asset_keys
    )

    # We explicitly use node_check_specs_by_output_name because it contains every single check spec, not just those selected in the currently
    # executing subset.
    checks_targeting_selected_sources = get_checks_on_sources_upstream_of_selected_assets(
        assets_def=assets_def, selected_asset_keys=context.selected_asset_keys
    )
    selected_check_keys = {*context.selected_asset_check_keys, *checks_targeting_selected_sources}

    # if all asset checks for the subsetted assets are selected, then we can just select the
    # assets and use indirect selection for the tests. We verify that
    # 1. all the selected checks are for selected assets
    # 2. no checks for selected assets are excluded
    # This also means we'll run any singular tests.
    selected_checks_on_non_selected_assets = {
        check_key
        for check_key in selected_check_keys
        if check_key.asset_key not in context.selected_asset_keys
    }
    all_check_keys = {
        check_spec.key for check_spec in assets_def.node_check_specs_by_output_name.values()
    }
    excluded_checks = all_check_keys.difference(selected_check_keys)
    excluded_checks_on_selected_assets = [
        check_key
        for check_key in excluded_checks
        if check_key.asset_key in context.selected_asset_keys
    ]

    # note that this will always be false if checks are disabled (which means the assets_def has no
    # check specs)
    if excluded_checks_on_selected_assets:
        # select all assets and tests explicitly, and turn off indirect selection. This risks
        # hitting the CLI argument length limit, but in the common scenarios that can be launched from the UI
        # (all checks disabled, only one check and no assets) it's not a concern.
        # Since we're setting DBT_INDIRECT_SELECTION=empty, we won't run any singular tests.
        selected_dbt_resources = [
            *selected_asset_resources,
            *get_dbt_test_names_for_check_keys(
                dagster_dbt_translator, manifest, assets_def, context.selected_asset_check_keys
            ),
        ]
        indirect_selection_override = DBT_EMPTY_INDIRECT_SELECTION
        logger.info(
            "Overriding default `DBT_INDIRECT_SELECTION` "
            f"{current_dbt_indirect_selection_env or 'eager'} with "
            f"`{indirect_selection_override}` due to additional checks "
            f"{', '.join([c.to_user_string() for c in selected_checks_on_non_selected_assets])} "
            f"and excluded checks {', '.join([c.to_user_string() for c in excluded_checks_on_selected_assets])}."
        )
    elif selected_checks_on_non_selected_assets:
        # explicitly select the tests that won't be run via indirect selection
        selected_dbt_resources = [
            *selected_asset_resources,
            *get_dbt_test_names_for_check_keys(
                dagster_dbt_translator,
                manifest,
                assets_def,
                selected_checks_on_non_selected_assets,
            ),
        ]
        indirect_selection_override = None
    else:
        selected_dbt_resources = selected_asset_resources
        indirect_selection_override = None

    logger.info(
        "A dbt subsetted execution is being performed. Overriding default dbt selection"
        f" arguments `{default_dbt_selection}` with arguments: `{selected_dbt_resources}`."
    )

    # Take the union of all the selected resources.
    # https://docs.getdbt.com/reference/node-selection/set-operators#unions
    union_selected_dbt_resources = ["--select"] + [" ".join(selected_dbt_resources)]

    return union_selected_dbt_resources, indirect_selection_override


def get_dbt_resource_names_for_asset_keys(
    translator: "DagsterDbtTranslator",
    manifest: Mapping[str, Any],
    assets_def: AssetsDefinition,
    asset_keys: Iterable[AssetKey],
) -> Sequence[str]:
    dbt_resource_props_gen = (
        get_node(
            manifest,
            assets_def.get_asset_spec(key).metadata[DAGSTER_DBT_UNIQUE_ID_METADATA_KEY],
        )
        for key in asset_keys
    )

    # Explicitly select a dbt resource by its file name.
    # https://docs.getdbt.com/reference/node-selection/methods#the-file-method
    if translator.settings.enable_dbt_selection_by_name:
        return [
            Path(dbt_resource_props["original_file_path"]).stem
            for dbt_resource_props in dbt_resource_props_gen
        ]

    # Explictly select a dbt resource by its fully qualified name (FQN).
    # https://docs.getdbt.com/reference/node-selection/methods#the-file-or-fqn-method
    return [".".join(dbt_resource_props["fqn"]) for dbt_resource_props in dbt_resource_props_gen]


def get_dbt_test_names_for_check_keys(
    translator: "DagsterDbtTranslator",
    manifest: Mapping[str, Any],
    assets_def: AssetsDefinition,
    check_keys: Iterable[AssetCheckKey],
) -> Sequence[str]:
    dbt_resource_props_gen = (
        get_node(
            manifest,
            (assets_def.get_spec_for_check_key(key).metadata or {})[
                DAGSTER_DBT_UNIQUE_ID_METADATA_KEY
            ],
        )
        for key in check_keys
    )
    # Explicitly select a dbt test by its test name.
    # https://docs.getdbt.com/reference/node-selection/test-selection-examples#more-complex-selection.
    if translator.settings.enable_dbt_selection_by_name:
        return [asset_check_key.name for asset_check_key in check_keys]

    # Explictly select a dbt test by its fully qualified name (FQN).
    # https://docs.getdbt.com/reference/node-selection/methods#the-file-or-fqn-method
    return [".".join(dbt_resource_props["fqn"]) for dbt_resource_props in dbt_resource_props_gen]


def get_node(manifest: Mapping[str, Any], unique_id: str) -> Mapping[str, Any]:
    """Find a node by unique_id in manifest_json."""
    if unique_id in manifest["nodes"]:
        return manifest["nodes"][unique_id]

    if unique_id in manifest["sources"]:
        return manifest["sources"][unique_id]

    if unique_id in manifest["exposures"]:
        return manifest["exposures"][unique_id]

    if unique_id in manifest["metrics"]:
        return manifest["metrics"][unique_id]

    if unique_id in manifest.get("semantic_models", {}):
        return manifest["semantic_models"][unique_id]

    if unique_id in manifest.get("saved_queries", {}):
        return manifest["saved_queries"][unique_id]

    if unique_id in manifest.get("unit_tests", {}):
        return manifest["unit_tests"][unique_id]

    check.failed(f"Could not find {unique_id} in dbt manifest")
