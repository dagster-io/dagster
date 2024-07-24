from typing import Mapping, Optional, Sequence

from dagster import (
    AssetKey,
    AssetsDefinition,
    AssetSelection,
    DefaultScheduleStatus,
    RunConfig,
    ScheduleDefinition,
    define_asset_job,
)


def dagster_name_fn(table_id: str) -> str:
    return table_id.replace(".", "_").replace("-", "_").replace("*", "_star")


def default_asset_key_fn(fqn: str) -> AssetKey:
    """Get the asset key for an sdf asset. An Sdf asset's key is its fully qualified name."""
    return AssetKey(fqn.split("."))


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

            @sdf_assets(manifest=...)
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
