import textwrap
from pathlib import Path
from typing import AbstractSet, Any, Dict, Mapping, Optional, Sequence

from dagster import (
    AssetCheckKey,
    AssetKey,
    AssetsDefinition,
    AssetSelection,
    DefaultScheduleStatus,
    RunConfig,
    ScheduleDefinition,
    define_asset_job,
)

from dagster_sdf.constants import SDF_TARGET_DIR


def dagster_name_fn(catalog: str, schema: str, table: str) -> str:
    fmt_catalog = catalog.replace(".", "_").replace("-", "_").replace("*", "_star")
    fmt_schema = schema.replace(".", "_").replace("-", "_").replace("*", "_star")
    fmt_table = table.replace(".", "_").replace("-", "_").replace("*", "_star")
    return f"{fmt_catalog}__{fmt_schema}__{fmt_table}"


def default_asset_key_fn(catalog: str, schema: str, table: str) -> AssetKey:
    """Get the asset key for an sdf asset. An Sdf asset's key is its fully qualified name."""
    return AssetKey([catalog, schema, table])


def default_asset_check_key_fn(catalog: str, schema: str, table: str) -> AssetCheckKey:
    """Get the asset check key for an sdf asset. An Sdf asset's check key is its fully qualified name."""
    # If table_name starts with "test_", this is a column or table test (to be updated with something more formal)
    if table.lower().startswith("test_"):
        asset_key = AssetKey([catalog, schema, table[5:]])
    else:
        asset_key = AssetKey([catalog, schema, table])
    return AssetCheckKey(
        name="test",
        asset_key=asset_key,
    )


def build_schedule_from_sdf_selection(
    _: Sequence[AssetsDefinition],
    job_name: str,
    cron_schedule: str,
    schedule_name: Optional[str] = None,
    tags: Optional[Mapping[str, str]] = None,
    config: Optional[RunConfig] = None,
    execution_timezone: Optional[str] = None,
    default_status: DefaultScheduleStatus = DefaultScheduleStatus.STOPPED,
) -> ScheduleDefinition:
    """Build a schedule to materialize a specified set of sdf models (Currently Limited to All).

    Args:
        job_name (str): The name of the job to materialize the sdf models.
        cron_schedule (str): The cron schedule to define the schedule.
        schedule_name (Optional[str]): The name of the sdf schedule to create.
        tags (Optional[Mapping[str, str]]): A dictionary of tags (string key-value pairs) to attach
            to the scheduled runs.
        config (Optional[RunConfig]): The config that parameterizes the execution of this schedule.
        execution_timezone (Optional[str]): Timezone in which the schedule should run.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".

    Returns:
        ScheduleDefinition: A definition to materialize the selected sdf models on a cron schedule.

    Examples:
        .. code-block:: python

            from dagster_sdf import sdf_assets, build_schedule_from_sdf_selection

            @sdf_assets(workspace=...)
            def all_sdf_assets():
                ...

            daily_sdf_assets_schedule = build_schedule_from_sdf_selection(
                [all_sdf_assets],
                job_name="all_sdf_assets",
                cron_schedule="0 0 * * *",
            )
    """
    return ScheduleDefinition(
        name=schedule_name,
        cron_schedule=cron_schedule,
        job=define_asset_job(
            name=job_name,
            selection=AssetSelection.all(),
            config=config,
            tags=tags,
        ),
        execution_timezone=execution_timezone,
        default_status=default_status,
    )


def get_asset_key_for_table_id(sdf_assets: Sequence[AssetsDefinition], table_id: str) -> AssetKey:
    """Returns the corresponding Dagster asset key for an sdf table.

    Args:
        table_id (str): The fqn of the the sdf table.

    Raises:
        DagsterInvalidInvocationError: If the source has more than one table.

    Returns:
        AssetKey: The corresponding Dagster asset key.

    Examples:
        .. code-block:: python

            from dagster import asset
            from dagster_sdf import sdf_assets, get_asset_key_for_table_id

            @sdf_assets(workspace=...)
            def all_sdf_assets():
                ...

            @asset(key=get_asset_key_for_table_id([all_sdf_assets], "my_source"))
            def upstream_python_asset():
                ...
    """
    # Strip table_id of any quotes
    table_id = table_id.replace('"', "").replace("`", "")
    asset_keys_by_output_name = {}
    for sdf_asset in sdf_assets:
        for name, key in sdf_asset.keys_by_output_name.items():
            key_table_id = ".".join(key.path)
            if key_table_id == table_id:
                asset_keys_by_output_name[name] = key

    if len(asset_keys_by_output_name) > 1:
        raise KeyError(
            f"Table {table_id} has more than one table associated with two or more unique dagster asset names:"
            f" {asset_keys_by_output_name.keys()}."
        )
    if not asset_keys_by_output_name:
        raise KeyError(f"Table {table_id} not found in the provided sdf assets.")
    return next(iter(asset_keys_by_output_name.values()))


def get_output_dir(target_dir: Path, environment: str) -> Path:
    return target_dir.joinpath(SDF_TARGET_DIR, environment)


def get_info_schema_dir(target_dir: Path, environment: str) -> Path:
    return get_output_dir(target_dir, environment).joinpath(
        "data", "system", "information_schema::sdf"
    )


def get_materialized_sql_dir(target_dir: Path, environment: str) -> Path:
    return get_output_dir(target_dir, environment).joinpath("materialized")


def get_table_path_from_parts(catalog_name: str, schema_name: str, table_name: str) -> Path:
    return Path(catalog_name.lower(), schema_name.lower(), table_name.lower())


def _read_sql_file(path_to_file: Path) -> str:
    with open(path_to_file, "r") as file:
        return textwrap.indent(file.read().strip(), "    ")


def default_description_fn(
    table_row: Dict[str, Any],
    workspace_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    enable_raw_sql_description: bool = True,
    enable_materialized_sql_description: bool = True,
) -> str:
    description_sections = [
        table_row["description"] or f"sdf {table_row['materialization']} {table_row['table_id']}",
    ]
    if enable_raw_sql_description:
        if workspace_dir is None:
            raise ValueError("workspace_dir must be provided to enable raw SQL description.")
        path_to_file = None
        for source_location in table_row["source_locations"]:
            if source_location.endswith(".sql"):
                path_to_file = workspace_dir.joinpath(source_location)
                break
        if path_to_file is not None and path_to_file.exists():
            description_sections.append(f"#### Raw SQL:\n```\n{_read_sql_file(path_to_file)}\n```")
    if enable_materialized_sql_description:
        if output_dir is None:
            raise ValueError("output_dir must be provided to enable materialized SQL description.")
        path_to_file = (
            output_dir.joinpath("materialized")
            .joinpath(
                get_table_path_from_parts(
                    table_row["catalog_name"], table_row["schema_name"], table_row["table_name"]
                )
            )
            .with_suffix(".sql")
        )
        if path_to_file.exists():
            description_sections.append(
                f"#### Materialized SQL:\n```\n{_read_sql_file(path_to_file)}\n```"
            )
    return "\n\n".join(filter(None, description_sections))


def get_test_prefix(table_dialect: str) -> str:
    if table_dialect == "snowflake":
        return "TEST_"
    else:
        return "test_"


def exists_in_selected(
    catalog_name: str,
    schema_name: str,
    table_name: str,
    purpose: str,
    dialect: str,
    selected_output_names: AbstractSet[str],
    asset_checks_enabled: bool,
) -> bool:
    asset_output_name = dagster_name_fn(catalog_name, schema_name, table_name)
    # If asset checks are enabled, ensure tests are only yielded for selected assets
    if asset_checks_enabled:
        # Strip test_name_prefix from start of table_id if it exists
        if purpose == "test":
            test_name_prefix = get_test_prefix(dialect)
            asset_output_name = (
                dagster_name_fn(catalog_name, schema_name, table_name[len(test_name_prefix) :])
                if table_name.startswith(test_name_prefix)
                else asset_output_name
            )

    if asset_output_name in selected_output_names:
        return True
    else:
        return False
