import glob
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Callable, Optional

import click

from dagster import (
    DagsterInvariantViolationError,
    __version__ as dagster_version,
)
from dagster._cli.utils import (
    assert_no_remaining_opts,
    get_instance_for_cli,
    validate_dagster_home_is_set,
    validate_repo_has_defined_schedules,
)
from dagster._cli.workspace.cli_target import (
    RepositoryOpts,
    WorkspaceOpts,
    get_repository_from_cli_opts,
    repository_options,
    workspace_options,
)
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation import RemoteRepository
from dagster._core.scheduler.instigation import InstigatorStatus
from dagster._core.scheduler.scheduler import DagsterDaemonScheduler
from dagster._utils import PrintFn


@click.group(name="schedule")
def schedule_cli():
    """Commands for working with Dagster schedules."""


@schedule_cli.command(
    name="preview", help="Preview changes that will be performed by `dagster schedule up`."
)
@workspace_options
@repository_options
def schedule_preview_command(**opts: object):
    workspace_opts = WorkspaceOpts.extract_from_cli_options(opts)
    repository_opts = RepositoryOpts.extract_from_cli_options(opts)
    assert_no_remaining_opts(opts)
    return execute_preview_command(workspace_opts, repository_opts, click.echo)


def execute_preview_command(
    workspace_opts: WorkspaceOpts, repository_opts: RepositoryOpts, print_fn: PrintFn
):
    with (
        get_instance_for_cli() as instance,
        _get_repo(workspace_opts, repository_opts, instance) as repo,
    ):
        print_changes(repo, instance, print_fn, preview=True)


@schedule_cli.command(
    name="list",
    help="List all schedules that correspond to a repository.",
)
@click.option(
    "--running", "running_filter", help="Filter for running schedules", is_flag=True, default=False
)
@click.option(
    "--stopped", "stopped_filter", help="Filter for stopped schedules", is_flag=True, default=False
)
@click.option(
    "--name",
    "name_filter",
    help="Only display schedule schedule names",
    is_flag=True,
    default=False,
)
@workspace_options
@repository_options
def schedule_list_command(
    running_filter: bool, stopped_filter: bool, name_filter: bool, **other_opts: object
):
    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    repository_opts = RepositoryOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)
    return execute_list_command(
        running_filter=running_filter,
        stopped_filter=stopped_filter,
        name_filter=name_filter,
        workspace_opts=workspace_opts,
        repository_opts=repository_opts,
        print_fn=click.echo,
    )


def execute_list_command(
    *,
    running_filter: bool,
    stopped_filter: bool,
    name_filter: bool,
    workspace_opts: WorkspaceOpts,
    repository_opts: RepositoryOpts,
    print_fn: PrintFn,
):
    with (
        get_instance_for_cli() as instance,
        _get_repo(workspace_opts, repository_opts, instance) as repo,
    ):
        if not name_filter:
            title = f"Repository {repo.name}"
            print_fn(title)
            print_fn("*" * len(title))

        repo_schedules = repo.get_schedules()
        stored_schedules_by_origin_id = {
            stored_schedule_state.instigator_origin_id: stored_schedule_state
            for stored_schedule_state in instance.all_instigator_state(
                repo.get_remote_origin_id(),
                repo.selector_id,
                instigator_type=InstigatorType.SCHEDULE,
            )
        }

        first = True

        for schedule in repo_schedules:
            schedule_state = schedule.get_current_instigator_state(
                stored_schedules_by_origin_id.get(schedule.get_remote_origin_id())
            )

            if running_filter and not schedule_state.is_running:
                continue
            if stopped_filter and schedule_state.is_running:
                continue

            if name_filter:
                print_fn(schedule.name)
                continue

            status = "RUNNING" if schedule_state.is_running else "STOPPED"
            schedule_title = f"Schedule: {schedule.name} [{status}]"
            if not first:
                print_fn("*" * len(schedule_title))

            first = False

            print_fn(schedule_title)
            print_fn(f"Cron Schedule: {schedule.cron_schedule}")


@schedule_cli.command(name="start", help="Start an existing schedule.")
@click.argument("schedule_name", required=False)
@click.option("--start-all", help="start all schedules", is_flag=True, default=False)
@workspace_options
@repository_options
def schedule_start_command(schedule_name: Optional[str], start_all: bool, **other_opts: object):
    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    repository_opts = RepositoryOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)
    if schedule_name is None and start_all is False:
        print(  # noqa: T201
            "Noop: dagster schedule start was called without any arguments specifying which "
            "schedules to start. Pass a schedule name or the --start-all flag to start schedules."
        )
        return
    return execute_start_command(
        schedule_name=schedule_name,
        start_all=start_all,
        workspace_opts=workspace_opts,
        repository_opts=repository_opts,
        print_fn=click.echo,
    )


def execute_start_command(
    *,
    schedule_name: Optional[str],
    start_all: bool,
    workspace_opts: WorkspaceOpts,
    repository_opts: RepositoryOpts,
    print_fn: PrintFn,
):
    with (
        get_instance_for_cli() as instance,
        _get_repo(workspace_opts, repository_opts, instance) as repo,
    ):
        if start_all:
            for remote_schedule in repo.get_schedules():
                try:
                    instance.start_schedule(remote_schedule)
                except DagsterInvariantViolationError as ex:
                    raise click.UsageError(ex)  # pyright: ignore[reportArgumentType]

            print_fn(f"Started all schedules for repository {repo.name}")
        else:
            if not schedule_name:
                raise click.UsageError("Missing schedule name")
            try:
                instance.start_schedule(repo.get_schedule(schedule_name))
            except DagsterInvariantViolationError as ex:
                raise click.UsageError(ex)  # pyright: ignore[reportArgumentType]

            print_fn(f"Started schedule {schedule_name}")


@schedule_cli.command(name="stop", help="Stop an existing schedule.")
@click.argument("schedule_name")
@workspace_options
@repository_options
def schedule_stop_command(schedule_name: str, **other_opts: object):
    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    repository_opts = RepositoryOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)
    return execute_stop_command(
        schedule_name=schedule_name,
        workspace_opts=workspace_opts,
        repository_opts=repository_opts,
        print_fn=click.echo,
    )


def execute_stop_command(
    *,
    schedule_name: str,
    workspace_opts: WorkspaceOpts,
    repository_opts: RepositoryOpts,
    print_fn: PrintFn,
    instance: Optional[DagsterInstance] = None,
):
    with (
        get_instance_for_cli() as instance,
        _get_repo(workspace_opts, repository_opts, instance) as repo,
    ):
        try:
            remote_schedule = repo.get_schedule(schedule_name)
            instance.stop_schedule(
                remote_schedule.get_remote_origin_id(),
                remote_schedule.selector_id,
                remote_schedule,
            )
        except DagsterInvariantViolationError as ex:
            raise click.UsageError(ex)  # pyright: ignore[reportArgumentType]

        print_fn(f"Stopped schedule {schedule_name}")


@schedule_cli.command(name="logs", help="Get logs for a schedule.")
@click.argument("schedule_name", required=False)
@workspace_options
@repository_options
def schedule_logs_command(schedule_name: Optional[str], **other_opts: object):
    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    repository_opts = RepositoryOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)
    if schedule_name is None:
        print(  # noqa: T201
            "Noop: dagster schedule logs was called without any arguments specifying which "
            "schedules to retrieve logs for. Pass a schedule name"
        )
        return
    return execute_logs_command(
        schedule_name=schedule_name,
        workspace_opts=workspace_opts,
        repository_opts=repository_opts,
        print_fn=click.echo,
    )


def execute_logs_command(
    *,
    schedule_name: str,
    workspace_opts: WorkspaceOpts,
    repository_opts: RepositoryOpts,
    print_fn: PrintFn,
    instance: Optional[DagsterInstance] = None,
):
    with (
        get_instance_for_cli() as instance,
        _get_repo(workspace_opts, repository_opts, instance) as repo,
    ):
        if isinstance(instance.scheduler, DagsterDaemonScheduler):
            return print_fn(
                "This command is deprecated for the DagsterDaemonScheduler. "
                "Logs for the DagsterDaemonScheduler written to the process output. "
                "For help troubleshooting the Daemon Scheduler, see "
                "https://docs.dagster.io/guides/automate/schedules/troubleshooting-schedules"
            )

        logs_path = os.path.join(
            instance.logs_path_for_schedule(repo.get_schedule(schedule_name).get_remote_origin_id())
        )

        logs_directory = os.path.dirname(logs_path)
        result_files = glob.glob(f"{logs_directory}/*.result")
        most_recent_log = max(result_files, key=os.path.getctime) if result_files else None

        output = ""

        title = "Scheduler Logs:"
        output += "{title}\n{sep}\n{info}\n".format(
            title=title,
            sep="=" * len(title),
            info=logs_path,
        )

        title = (
            "Schedule Execution Logs:"
            "\nEvent logs from schedule execution. "
            "Errors that caused schedule executions to not run or fail can be found here. "
        )
        most_recent_info = (
            f"\nMost recent execution log: {most_recent_log}" if most_recent_log else ""
        )
        info = f"All execution logs: {logs_directory}{most_recent_info}"
        output += "\n{title}\n{sep}\n{info}\n".format(
            title=title,
            sep="=" * len(title),
            info=info,
        )

        print_fn(output)


@schedule_cli.command(name="restart", help="Restart a running schedule.")
@click.argument("schedule_name", required=False)
@click.option(
    "--restart-all-running",
    help="restart previously running schedules",
    is_flag=True,
    default=False,
)
@workspace_options
@repository_options
def schedule_restart_command(schedule_name: Optional[str], restart_all_running: bool, **other_opts):
    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    repository_opts = RepositoryOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)
    return execute_restart_command(
        schedule_name=schedule_name,
        restart_all_running=restart_all_running,
        workspace_opts=workspace_opts,
        repository_opts=repository_opts,
        print_fn=click.echo,
    )


def execute_restart_command(
    *,
    schedule_name: Optional[str],
    restart_all_running: bool,
    workspace_opts: WorkspaceOpts,
    repository_opts: RepositoryOpts,
    print_fn: PrintFn,
):
    with (
        get_instance_for_cli() as instance,
        _get_repo(workspace_opts, repository_opts, instance) as repo,
    ):
        if restart_all_running:
            for schedule_state in instance.all_instigator_state(
                repo.get_remote_origin_id(),
                repo.selector_id,
                InstigatorType.SCHEDULE,
            ):
                if schedule_state.status == InstigatorStatus.RUNNING:
                    try:
                        remote_schedule = repo.get_schedule(schedule_state.instigator_name)
                        instance.stop_schedule(
                            schedule_state.instigator_origin_id,
                            remote_schedule.selector_id,
                            remote_schedule,
                        )
                        instance.start_schedule(remote_schedule)
                    except DagsterInvariantViolationError as ex:
                        raise click.UsageError(ex)  # pyright: ignore[reportArgumentType]

            print_fn(f"Restarted all running schedules for repository {repo.name}")
        else:
            if not schedule_name:
                raise click.UsageError("Missing schedule name")
            remote_schedule = repo.get_schedule(schedule_name)
            schedule_state = instance.get_instigator_state(
                remote_schedule.get_remote_origin_id(),
                remote_schedule.selector_id,
            )
            if schedule_state is not None and schedule_state.status != InstigatorStatus.RUNNING:
                click.UsageError(
                    f"Cannot restart a schedule {schedule_state.instigator_name} because is not currently running"
                )

            try:
                instance.stop_schedule(
                    schedule_state.instigator_origin_id,  # pyright: ignore[reportOptionalMemberAccess]
                    remote_schedule.selector_id,
                    remote_schedule,
                )
                instance.start_schedule(remote_schedule)
            except DagsterInvariantViolationError as ex:
                raise click.UsageError(ex)  # pyright: ignore[reportArgumentType]

            print_fn(f"Restarted schedule {schedule_name}")


@schedule_cli.command(name="wipe", help="Delete the schedule history and turn off all schedules.")
def schedule_wipe_command():
    return execute_wipe_command(click.echo)


def execute_wipe_command(print_fn: PrintFn):
    with get_instance_for_cli() as instance:
        confirmation = click.prompt(
            "Are you sure you want to turn off all schedules and delete all schedule history? Type"
            " DELETE"
        )
        if confirmation == "DELETE":
            instance.wipe_all_schedules()
            print_fn("Turned off all schedules and deleted all schedule history")
        else:
            print_fn("Exiting without turning off schedules or deleting schedule history")


@schedule_cli.command(name="debug", help="Debug information about the scheduler.")
def schedule_debug_command():
    return execute_debug_command(click.echo)


def execute_debug_command(print_fn: PrintFn):
    with get_instance_for_cli() as instance:
        debug_info = instance.scheduler_debug_info()

        output = ""

        errors = debug_info.errors
        if len(errors):
            title = "Errors (Run `dagster schedule up` to resolve)"
            output += "\n{title}\n{sep}\n{info}\n\n".format(
                title=title,
                sep="=" * len(title),
                info="\n".join(debug_info.errors),
            )

        title = "Scheduler Configuration"
        output += "{title}\n{sep}\n{info}\n".format(
            title=title,
            sep="=" * len(title),
            info=debug_info.scheduler_config_info,
        )

        title = "Scheduler Info"
        output += "{title}\n{sep}\n{info}\n".format(
            title=title, sep="=" * len(title), info=debug_info.scheduler_info
        )

        title = "Scheduler Storage Info"
        output += "\n{title}\n{sep}\n{info}\n".format(
            title=title,
            sep="=" * len(title),
            info="\n".join(debug_info.schedule_storage),
        )

        print_fn(output)


# ########################
# ##### HELPERS
# ########################


def print_changes(
    remote_repository: RemoteRepository,
    instance: DagsterInstance,
    print_fn: Callable[[object], None] = print,
    preview: bool = False,
) -> None:
    debug_info = instance.scheduler_debug_info()
    errors = debug_info.errors
    schedules = remote_repository.get_schedules()
    schedule_states = instance.all_instigator_state(
        remote_repository.get_remote_origin_id(),
        remote_repository.selector_id,
        InstigatorType.SCHEDULE,
    )
    schedules_dict = {s.get_remote_origin_id(): s for s in schedules}
    schedule_states_dict = {s.instigator_origin_id: s for s in schedule_states}

    schedule_origin_ids = set(schedules_dict.keys())
    schedule_state_ids = set(schedule_states_dict.keys())

    added_schedules = schedule_origin_ids - schedule_state_ids
    removed_schedules = schedule_state_ids - schedule_origin_ids

    changed_schedules = []
    for schedule_origin_id in schedule_origin_ids & schedule_state_ids:
        schedule_state = schedule_states_dict[schedule_origin_id]
        schedule = schedules_dict[schedule_origin_id]
        if schedule_state.instigator_data.cron_schedule != schedule.cron_schedule:  # type: ignore
            changed_schedules.append(schedule_origin_id)

    if not errors and not added_schedules and not changed_schedules and not removed_schedules:
        if preview:
            print_fn(click.style("No planned changes to schedules.", fg="magenta", bold=True))
            print_fn(f"{len(schedules)} schedules will remain unchanged")
        else:
            print_fn(click.style("No changes to schedules.", fg="magenta", bold=True))
            print_fn(f"{len(schedules)} schedules unchanged")
        return

    if errors:
        print_fn(
            click.style(
                "Planned Error Fixes:" if preview else "Errors Resolved:", fg="magenta", bold=True
            )
        )
        print_fn("\n".join(debug_info.errors))

    if added_schedules or changed_schedules or removed_schedules:
        print_fn(
            click.style(
                "Planned Schedule Changes:" if preview else "Changes:", fg="magenta", bold=True
            )
        )

    for schedule_origin_id in added_schedules:
        print_fn(
            click.style(
                f"  + {schedules_dict[schedule_origin_id].name} (add) [{schedule_origin_id}]",
                fg="green",
            )
        )

    for schedule_origin_id in changed_schedules:
        schedule_state = schedule_states_dict[schedule_origin_id]
        schedule = schedules_dict[schedule_origin_id]

        print_fn(
            click.style(
                f"  ~ {schedule.name} (update) [{schedule_origin_id}]",
                fg="yellow",
            )
        )
        print_fn(
            click.style("\t cron_schedule: ", fg="yellow")
            + click.style(schedule_state.instigator_data.cron_schedule, fg="red")  # type: ignore
            + " => "
            + click.style(schedule.cron_schedule, fg="green")
        )

    for schedule_origin_id in removed_schedules:
        print_fn(
            click.style(
                f"  - {schedule_states_dict[schedule_origin_id].instigator_name} (delete) [{schedule_origin_id}]",
                fg="red",
            )
        )


@contextmanager
def _get_repo(
    workspace_opts: WorkspaceOpts, repository_opts: RepositoryOpts, instance: DagsterInstance
) -> Iterator[RemoteRepository]:
    with get_repository_from_cli_opts(
        instance=instance,
        version=dagster_version,
        workspace_opts=workspace_opts,
        repository_opts=repository_opts,
    ) as repo:
        validate_repo_has_defined_schedules(repo)
        validate_dagster_home_is_set()
        yield repo
