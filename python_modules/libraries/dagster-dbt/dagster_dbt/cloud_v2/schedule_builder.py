from collections.abc import Mapping, Sequence
from typing import Any, Optional

from dagster import AssetsDefinition, ScheduleDefinition, get_dagster_logger
from dagster._annotations import preview
from dbt.cli import dbt_cli
from dbt.cli.options import MultiOption

from dagster_dbt.asset_utils import (
    DAGSTER_DBT_EXCLUDE_METADATA_KEY,
    DAGSTER_DBT_INDIRECT_SELECTION_METADATA_KEY,
    DAGSTER_DBT_OTHER_ARGS_METADATA_KEY,
    DAGSTER_DBT_SELECT_METADATA_KEY,
    build_schedule_from_dbt_selection,
)
from dagster_dbt.cloud_v2.resources import (
    DBT_CLOUD_DEFAULT_EXCLUDE,
    DBT_CLOUD_DEFAULT_SELECT,
    DbtCloudWorkspace,
)
from dagster_dbt.cloud_v2.types import DbtCloudJob

logger = get_dagster_logger()


SELECT_ARGUMENT_KEY = "select"
EXCLUDE_ARGUMENT_KEY = "exclude"
INDIRECT_SELECTION_KEY = "indirect_selection"


def execute_step_to_command_args(execute_step: str) -> Sequence[str]:
    execute_step_parts = execute_step.split()
    if execute_step_parts[0] == "dbt":
        execute_step_parts.pop(0)
    return execute_step_parts


def multi_option_arg_value_to_str(arg_value: Sequence[tuple[str]]) -> str:
    return " ".join(arg_value[0])


def reconstruct_args_str(
    args_dict: Mapping[str, Any], class_by_arg_name: Mapping[str, Any]
) -> Optional[str]:
    reconstructed_args = []
    if args_dict:
        for arg_name, arg_value in args_dict.items():
            clazz = class_by_arg_name[arg_name]

            if clazz == MultiOption:
                arg_value_as_str = multi_option_arg_value_to_str(arg_value=arg_value)
            else:
                if isinstance(arg_value, bool):
                    arg_value_as_str = None
                else:
                    arg_value_as_str = arg_value

            reconstructed_args.append(f"--{arg_name.replace('_', '-')}")
            if arg_value_as_str:
                reconstructed_args.append(arg_value_as_str)
    return " ".join(reconstructed_args) if reconstructed_args else None


def execute_step_to_args(
    execute_step: str,
) -> tuple[str, Optional[str], Optional[str], Optional[str], Optional[str]]:
    command_args = execute_step_to_command_args(execute_step=execute_step)
    cli_ctx = dbt_cli.make_context(dbt_cli.name, command_args)
    sub_command_name, sub_command, sub_command_args = dbt_cli.resolve_command(cli_ctx, command_args)
    sub_command_ctx = sub_command.make_context(sub_command_name, sub_command_args)

    parser = sub_command.make_parser(sub_command_ctx)
    args_dict, _, args_order = parser.parse_args(command_args)
    class_by_arg_name = {arg.human_readable_name: arg.__class__ for arg in args_order}

    select = (
        multi_option_arg_value_to_str(args_dict.pop(SELECT_ARGUMENT_KEY))
        if SELECT_ARGUMENT_KEY in args_dict
        else None
    )
    exclude = (
        multi_option_arg_value_to_str(args_dict.pop(EXCLUDE_ARGUMENT_KEY))
        if EXCLUDE_ARGUMENT_KEY in args_dict
        else None
    )
    indirect_selection = (
        args_dict.pop(INDIRECT_SELECTION_KEY) if INDIRECT_SELECTION_KEY in args_dict else None
    )
    other_args = reconstruct_args_str(args_dict=args_dict, class_by_arg_name=class_by_arg_name)

    return sub_command_name, select, exclude, indirect_selection, other_args


@preview
def build_schedules_from_dbt_cloud_workspace(
    dbt_cloud_assets: Sequence[AssetsDefinition], workspace: DbtCloudWorkspace
) -> Sequence[ScheduleDefinition]:
    """Build schedules to materialize dbt Cloud assets.
    These schedules replicate the behavior of the dbt Cloud jobs of the given dbt Cloud workspace.

    Args:
        dbt_cloud_assets (List[AssetsDefinition]): The dbt Cloud assets for which to create the schedules.
        workspace (DbtCloudWorkspace): The dbt Cloud workspace.

    Returns:
        List[ScheduleDefinition]: A list of schedule definitions replicating the dbt Cloud jobs of the given workspace.
    """
    [dbt_cloud_assets_definition] = dbt_cloud_assets

    dbt_assets_select = dbt_cloud_assets_definition.op.tags[DAGSTER_DBT_SELECT_METADATA_KEY]
    dbt_assets_exclude = dbt_cloud_assets_definition.op.tags[DAGSTER_DBT_EXCLUDE_METADATA_KEY]

    if (
        dbt_assets_select != DBT_CLOUD_DEFAULT_SELECT
        and dbt_assets_exclude != DBT_CLOUD_DEFAULT_EXCLUDE
    ):
        logger.warning(
            "Cannot create Dagster schedules with for dbt Cloud assets with custom dbt selection and exclusion args."
            "Returning an empty list."
        )
        return []

    workspace_data = workspace.get_or_fetch_workspace_data()
    schedules = []

    for job_details in workspace_data.jobs:
        job = DbtCloudJob.from_job_details(job_details=job_details)

        if job.id == workspace_data.adhoc_job_id:
            # We don't create a schedule for the Dagster ad hoc job
            continue

        if not job.has_single_non_empty_execute_step or not job.cron_schedule:
            logger.warning(f"Job {job.name} with ID {job.id} skipped.")
            if not job.has_single_non_empty_execute_step:
                logger.warning(
                    "dbt Cloud jobs must have a single and "
                    "non-empty execute step to be converted into Dagster schedules."
                )
            if not job.cron_schedule:
                logger.warning(
                    "dbt Cloud jobs must have an available cron schedule to be converted into Dagster schedules."
                )
            continue

        command, select, exclude, indirect_selection, other_args = execute_step_to_args(
            next(iter(job.execute_steps))
        )

        tags = {
            **(
                {DAGSTER_DBT_INDIRECT_SELECTION_METADATA_KEY: indirect_selection}
                if indirect_selection
                else {}
            ),
            **({DAGSTER_DBT_OTHER_ARGS_METADATA_KEY: other_args} if other_args else {}),
        }

        schedules.append(
            build_schedule_from_dbt_selection(
                dbt_assets=dbt_cloud_assets,
                job_name=job.name,
                cron_schedule=job.cron_schedule,
                dbt_select=select if select else DBT_CLOUD_DEFAULT_SELECT,
                dbt_exclude=exclude if exclude else DBT_CLOUD_DEFAULT_EXCLUDE,
                tags=tags if tags else None,
            )
        )

    return schedules
