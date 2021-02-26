import glob
import os

import click
from dagster import DagsterInvariantViolationError, check
from dagster.cli.workspace.cli_target import (
    get_external_repository_from_kwargs,
    repository_target_argument,
)
from dagster.core.definitions.job import JobType
from dagster.core.host_representation import ExternalRepository
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler.job import JobStatus
from dagster.core.scheduler.scheduler import DagsterDaemonScheduler


def create_schedule_cli_group():
    group = click.Group(name="schedule")
    group.add_command(schedule_list_command)
    group.add_command(schedule_up_command)
    group.add_command(schedule_preview_command)
    group.add_command(schedule_start_command)
    group.add_command(schedule_logs_command)
    group.add_command(schedule_stop_command)
    group.add_command(schedule_restart_command)
    group.add_command(schedule_wipe_command)
    group.add_command(schedule_debug_command)
    return group


def print_changes(external_repository, instance, print_fn=print, preview=False):
    debug_info = instance.scheduler_debug_info()
    errors = debug_info.errors
    external_schedules = external_repository.get_external_schedules()
    schedule_states = instance.all_stored_job_state(
        external_repository.get_external_origin_id(), JobType.SCHEDULE
    )
    external_schedules_dict = {s.get_external_origin_id(): s for s in external_schedules}
    schedule_states_dict = {s.job_origin_id: s for s in schedule_states}

    external_schedule_origin_ids = set(external_schedules_dict.keys())
    schedule_state_ids = set(schedule_states_dict.keys())

    added_schedules = external_schedule_origin_ids - schedule_state_ids
    removed_schedules = schedule_state_ids - external_schedule_origin_ids

    changed_schedules = []
    for schedule_origin_id in external_schedule_origin_ids & schedule_state_ids:
        schedule_state = schedule_states_dict[schedule_origin_id]
        external_schedule = external_schedules_dict[schedule_origin_id]
        if schedule_state.job_specific_data.cron_schedule != external_schedule.cron_schedule:
            changed_schedules.append(schedule_origin_id)

    if not errors and not added_schedules and not changed_schedules and not removed_schedules:
        if preview:
            print_fn(click.style("No planned changes to schedules.", fg="magenta", bold=True))
            print_fn("{num} schedules will remain unchanged".format(num=len(external_schedules)))
        else:
            print_fn(click.style("No changes to schedules.", fg="magenta", bold=True))
            print_fn("{num} schedules unchanged".format(num=len(external_schedules)))
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
                "  + {name} (add) [{id}]".format(
                    name=external_schedules_dict[schedule_origin_id].name, id=schedule_origin_id
                ),
                fg="green",
            )
        )

    for schedule_origin_id in changed_schedules:
        schedule_state = schedule_states_dict[schedule_origin_id]
        external_schedule = external_schedules_dict[schedule_origin_id]

        print_fn(
            click.style(
                "  ~ {name} (update) [{id}]".format(
                    name=external_schedule.name, id=schedule_origin_id
                ),
                fg="yellow",
            )
        )
        print_fn(
            click.style("\t cron_schedule: ", fg="yellow")
            + click.style(schedule_state.job_specific_data.cron_schedule, fg="red")
            + " => "
            + click.style(external_schedule.cron_schedule, fg="green")
        )

    for schedule_origin_id in removed_schedules:
        print_fn(
            click.style(
                "  - {name} (delete) [{id}]".format(
                    name=schedule_states_dict[schedule_origin_id].job_name, id=schedule_origin_id
                ),
                fg="red",
            )
        )


def check_repo_and_scheduler(repository, instance):
    check.inst_param(repository, "repository", ExternalRepository)
    check.inst_param(instance, "instance", DagsterInstance)

    repository_name = repository.name

    if not repository.get_external_schedules():
        raise click.UsageError(
            "There are no schedules defined for repository {name}.".format(name=repository_name)
        )

    no_scheduler_configured_message = (
        "A scheduler must be configured to run schedule commands."
        "You can resolve this error by defining a scheduler on your instance"
        "using your dagster.yaml, located in the $DAGSTER_HOME directory.\n"
        "For example, you can add the following lines in your dagster.yaml file:\n\n"
        "scheduler:\n"
        "\tmodule: dagster_cron.cron_scheduler\n"
        "\tclass: SystemCronScheduler\n"
    )

    if not os.getenv("DAGSTER_HOME"):
        raise click.UsageError(
            (
                "The environment variable $DAGSTER_HOME is not set. Dagster requires this "
                "environment variable to be set to an existing directory in your filesystem "
                "that contains your dagster instance configuration file (dagster.yaml).\n"
                "You can resolve this error by exporting the environment variable."
                "For example, you can run the following command in your shell or "
                "include it in your shell configuration file:\n"
                '\texport DAGSTER_HOME="~/dagster_home"'
                "\n\n"
            )
            + no_scheduler_configured_message
        )

    if not instance.scheduler:
        raise click.UsageError(no_scheduler_configured_message)


@click.command(
    name="preview", help="Preview changes that will be performed by `dagster schedule up"
)
@repository_target_argument
def schedule_preview_command(**kwargs):
    return execute_preview_command(kwargs, click.echo)


def execute_preview_command(cli_args, print_fn):
    with DagsterInstance.get() as instance:
        with get_external_repository_from_kwargs(cli_args) as external_repo:
            check_repo_and_scheduler(external_repo, instance)

            print_changes(external_repo, instance, print_fn, preview=True)


@click.command(
    name="up",
    help="Updates the internal dagster representation of schedules to match the list "
    "of ScheduleDefinitions defined in the repository. Use `dagster schedule up --preview` or "
    "`dagster schedule preview` to preview what changes will be applied. New ScheduleDefinitions "
    "will not start running by default when `up` is called. Use `dagster schedule start` and "
    "`dagster schedule stop` to start and stop a schedule. If a ScheduleDefinition is deleted, the "
    "corresponding running schedule will be stopped and deleted.",
)
@click.option("--preview", help="Preview changes", is_flag=True, default=False)
@repository_target_argument
def schedule_up_command(preview, **kwargs):
    return execute_up_command(preview, kwargs, click.echo)


def execute_up_command(preview, cli_args, print_fn):
    with DagsterInstance.get() as instance:
        with get_external_repository_from_kwargs(cli_args) as external_repo:
            check_repo_and_scheduler(external_repo, instance)

            print_changes(external_repo, instance, print_fn, preview=preview)
            if preview:
                return

            try:
                instance.reconcile_scheduler_state(external_repo)
            except DagsterInvariantViolationError as ex:
                raise click.UsageError(ex)


@click.command(
    name="list",
    help="List all schedules that correspond to a repository.",
)
@repository_target_argument
@click.option("--running", help="Filter for running schedules", is_flag=True, default=False)
@click.option("--stopped", help="Filter for stopped schedules", is_flag=True, default=False)
@click.option("--name", help="Only display schedule schedule names", is_flag=True, default=False)
def schedule_list_command(running, stopped, name, **kwargs):
    return execute_list_command(running, stopped, name, kwargs, click.echo)


def execute_list_command(running_filter, stopped_filter, name_filter, cli_args, print_fn):
    with DagsterInstance.get() as instance:
        with get_external_repository_from_kwargs(cli_args) as external_repo:
            check_repo_and_scheduler(external_repo, instance)

            repository_name = external_repo.name

            if not name_filter:
                title = "Repository {name}".format(name=repository_name)
                print_fn(title)
                print_fn("*" * len(title))

            first = True

            if running_filter:
                schedules = [
                    s
                    for s in instance.all_stored_job_state(
                        external_repo.get_external_origin_id(), job_type=JobType.SCHEDULE
                    )
                    if s.status == JobStatus.RUNNING
                ]
            elif stopped_filter:
                schedules = [
                    s
                    for s in instance.all_stored_job_state(
                        external_repo.get_external_origin_id(), job_type=JobType.SCHEDULE
                    )
                    if s.status == JobStatus.STOPPED
                ]
            else:
                schedules = instance.all_stored_job_state(
                    external_repo.get_external_origin_id(), job_type=JobType.SCHEDULE
                )

            for schedule_state in schedules:
                # If --name filter is present, only print the schedule name
                if name_filter:
                    print_fn(schedule_state.job_name)
                    continue

                flag = (
                    "[{status}]".format(status=schedule_state.status.value)
                    if schedule_state
                    else ""
                )
                schedule_title = "Schedule: {name} {flag}".format(
                    name=schedule_state.job_name, flag=flag
                )

                if not first:
                    print_fn("*" * len(schedule_title))
                first = False

                print_fn(schedule_title)
                print_fn(
                    "Cron Schedule: {cron_schedule}".format(
                        cron_schedule=schedule_state.job_specific_data.cron_schedule
                    )
                )


def extract_schedule_name(schedule_name):
    if schedule_name and not isinstance(schedule_name, str):
        if len(schedule_name) == 1:
            return schedule_name[0]
        else:
            check.failed(
                "Can only handle zero or one schedule args. Got {schedule_name}".format(
                    schedule_name=repr(schedule_name)
                )
            )


@click.command(name="start", help="Start an existing schedule")
@click.argument("schedule_name", nargs=-1)  # , required=True)
@click.option("--start-all", help="start all schedules", is_flag=True, default=False)
@repository_target_argument
def schedule_start_command(schedule_name, start_all, **kwargs):
    schedule_name = extract_schedule_name(schedule_name)
    if schedule_name is None and start_all is False:
        print(  # pylint: disable=print-call
            "Noop: dagster schedule start was called without any arguments specifying which "
            "schedules to start. Pass a schedule name or the --start-all flag to start schedules."
        )
        return
    return execute_start_command(schedule_name, start_all, kwargs, click.echo)


def execute_start_command(schedule_name, all_flag, cli_args, print_fn):
    with DagsterInstance.get() as instance:
        with get_external_repository_from_kwargs(cli_args) as external_repo:
            check_repo_and_scheduler(external_repo, instance)

            repository_name = external_repo.name

            if all_flag:
                for external_schedule in external_repo.get_external_schedules():
                    try:
                        instance.start_schedule_and_update_storage_state(external_schedule)
                    except DagsterInvariantViolationError as ex:
                        raise click.UsageError(ex)

                print_fn(
                    "Started all schedules for repository {repository_name}".format(
                        repository_name=repository_name
                    )
                )
            else:
                try:

                    instance.start_schedule_and_update_storage_state(
                        external_repo.get_external_schedule(schedule_name)
                    )
                except DagsterInvariantViolationError as ex:
                    raise click.UsageError(ex)

                print_fn("Started schedule {schedule_name}".format(schedule_name=schedule_name))


@click.command(name="stop", help="Stop an existing schedule")
@click.argument("schedule_name", nargs=-1)
@repository_target_argument
def schedule_stop_command(schedule_name, **kwargs):
    schedule_name = extract_schedule_name(schedule_name)
    return execute_stop_command(schedule_name, kwargs, click.echo)


def execute_stop_command(schedule_name, cli_args, print_fn, instance=None):
    with DagsterInstance.get() as instance:
        with get_external_repository_from_kwargs(cli_args) as external_repo:
            check_repo_and_scheduler(external_repo, instance)

            try:
                instance.stop_schedule_and_update_storage_state(
                    external_repo.get_external_schedule(schedule_name).get_external_origin_id()
                )
            except DagsterInvariantViolationError as ex:
                raise click.UsageError(ex)

            print_fn("Stopped schedule {schedule_name}".format(schedule_name=schedule_name))


@click.command(name="logs", help="Get logs for a schedule")
@click.argument("schedule_name", nargs=-1)
@repository_target_argument
def schedule_logs_command(schedule_name, **kwargs):
    schedule_name = extract_schedule_name(schedule_name)
    if schedule_name is None:
        print(  # pylint: disable=print-call
            "Noop: dagster schedule logs was called without any arguments specifying which "
            "schedules to retrieve logs for. Pass a schedule name"
        )
        return
    return execute_logs_command(schedule_name, kwargs, click.echo)


def execute_logs_command(schedule_name, cli_args, print_fn, instance=None):
    with DagsterInstance.get() as instance:
        with get_external_repository_from_kwargs(cli_args) as external_repo:
            check_repo_and_scheduler(external_repo, instance)

            if isinstance(instance.scheduler, DagsterDaemonScheduler):
                return print_fn(
                    "This command is deprecated for the DagsterDaemonScheduler. "
                    "Logs for the DagsterDaemonScheduler written to the process output. "
                    "For help troubleshooting the Daemon Scheduler, see "
                    "https://docs.dagster.io/troubleshooting/schedules"
                )

            logs_path = os.path.join(
                instance.logs_path_for_schedule(
                    external_repo.get_external_schedule(schedule_name).get_external_origin_id()
                )
            )

            logs_directory = os.path.dirname(logs_path)
            result_files = glob.glob("{}/*.result".format(logs_directory))
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
                "\nMost recent execution log: {}".format(most_recent_log) if most_recent_log else ""
            )
            info = "All execution logs: {}{}".format(logs_directory, most_recent_info)
            output += "\n{title}\n{sep}\n{info}\n".format(
                title=title,
                sep="=" * len(title),
                info=info,
            )

            print_fn(output)


@click.command(name="restart", help="Restart a running schedule")
@click.argument("schedule_name", nargs=-1)
@click.option(
    "--restart-all-running",
    help="restart previously running schedules",
    is_flag=True,
    default=False,
)
@repository_target_argument
def schedule_restart_command(schedule_name, restart_all_running, **kwargs):
    schedule_name = extract_schedule_name(schedule_name)
    return execute_restart_command(schedule_name, restart_all_running, kwargs, click.echo)


def execute_restart_command(schedule_name, all_running_flag, cli_args, print_fn):
    with DagsterInstance.get() as instance:
        with get_external_repository_from_kwargs(cli_args) as external_repo:
            check_repo_and_scheduler(external_repo, instance)

            repository_name = external_repo.name

            if all_running_flag:
                for schedule_state in instance.all_stored_job_state(
                    external_repo.get_external_origin_id(), JobType.SCHEDULE
                ):
                    if schedule_state.status == JobStatus.RUNNING:
                        try:
                            external_schedule = external_repo.get_external_schedule(
                                schedule_state.job_name
                            )
                            instance.stop_schedule_and_update_storage_state(
                                schedule_state.job_origin_id
                            )
                            instance.start_schedule_and_update_storage_state(external_schedule)
                        except DagsterInvariantViolationError as ex:
                            raise click.UsageError(ex)

                print_fn(
                    "Restarted all running schedules for repository {name}".format(
                        name=repository_name
                    )
                )
            else:
                external_schedule = external_repo.get_external_schedule(schedule_name)
                schedule_state = instance.get_job_state(external_schedule.get_external_origin_id())
                if schedule_state != None and schedule_state.status != JobStatus.RUNNING:
                    click.UsageError(
                        "Cannot restart a schedule {name} because is not currently running".format(
                            name=schedule_state.job_name
                        )
                    )

                try:
                    instance.stop_schedule_and_update_storage_state(schedule_state.job_origin_id)
                    instance.start_schedule_and_update_storage_state(external_schedule)
                except DagsterInvariantViolationError as ex:
                    raise click.UsageError(ex)

                print_fn("Restarted schedule {schedule_name}".format(schedule_name=schedule_name))


@click.command(name="wipe", help="Deletes schedule history and turns off all schedules.")
@repository_target_argument
def schedule_wipe_command(**kwargs):
    return execute_wipe_command(kwargs, click.echo)


def execute_wipe_command(cli_args, print_fn):
    with DagsterInstance.get() as instance:
        with get_external_repository_from_kwargs(cli_args) as external_repo:
            check_repo_and_scheduler(external_repo, instance)

            confirmation = click.prompt(
                "Are you sure you want to turn off all schedules and delete all schedule history? Type DELETE"
            )
            if confirmation == "DELETE":
                instance.wipe_all_schedules()
                print_fn("Turned off all schedules and deleted all schedule history")
            else:
                print_fn("Exiting without turning off schedules or deleting schedule history")


@click.command(name="debug", help="Debug information about the scheduler")
def schedule_debug_command():
    return execute_debug_command(click.echo)


def execute_debug_command(print_fn):
    with DagsterInstance.get() as instance:
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


schedule_cli = create_schedule_cli_group()
