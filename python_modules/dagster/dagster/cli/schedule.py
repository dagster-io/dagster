from __future__ import print_function

import sys

import click
import six

from dagster import DagsterInvariantViolationError, check
from dagster.cli.load_handle import handle_for_repo_cli_args
from dagster.core.instance import DagsterInstance
from dagster.utils import DEFAULT_REPOSITORY_YAML_FILENAME


def create_schedule_cli_group():
    group = click.Group(name="schedule")
    group.add_command(schedule_list_command)
    group.add_command(schedule_start_command)
    group.add_command(schedule_end_command)
    return group


# With the SystemCronScheduler, we currently only target a repository.yaml file since we need
# an absolute path to the repository that we can use in the cron job bash script. When using
# the combination of --python-file --fn-name flags, ExecutionTargetHandle doesn't contain an
# absolute path to the python file, but we can eventually change that to support these flags.
REPO_TARGET_WARNING = 'Can only use --repository-yaml/-y'


def apply_click_params(command, *click_params):
    for click_param in click_params:
        command = click_param(command)
    return command


def repository_target_argument(f):
    return apply_click_params(
        f,
        click.option(
            '--repository-yaml',
            '-y',
            type=click.Path(exists=True),
            help=('Path to config file. Defaults to ./{default_filename} not specified').format(
                default_filename=DEFAULT_REPOSITORY_YAML_FILENAME
            ),
        ),
    )


@click.command(
    name='list',
    help="[Experimental] List the schedules in a repository. {warning}".format(
        warning=REPO_TARGET_WARNING
    ),
)
@repository_target_argument
@click.option('--running', help="Filter for running schedules", is_flag=True, default=False)
@click.option('--name', help="Only display schedule schedule names", is_flag=True, default=False)
@click.option('--verbose', is_flag=True)
def schedule_list_command(running, name, verbose, **kwargs):
    return execute_list_command(running, name, verbose, kwargs, click.echo)


def execute_list_command(running_filter, name_filter, verbose, cli_args, print_fn):
    handle = handle_for_repo_cli_args(cli_args)
    repository = handle.build_repository_definition()
    schedule_dir = DagsterInstance.get().schedules_directory()

    scheduler = repository.build_scheduler(schedule_dir=schedule_dir)
    if not scheduler and not name_filter:
        print_fn("Scheduler not defined for repository {name}".format(name=repository.name))
        return

    if not name_filter:
        title = 'Repository {name}'.format(name=repository.name)
        print_fn(title)
        print_fn('*' * len(title))

    first = True
    for schedule in repository.get_all_schedules():
        is_running = scheduler.get_schedule_by_name(schedule.name)

        # If --running flag is present and the schedule is not running,
        # do not print
        if running_filter and not is_running:
            continue

        # If --name filter is present, only print the schedule name
        if name_filter:
            print_fn(schedule.name)
            continue

        running_flag = "[Running]" if is_running else ""
        schedule_title = 'Schedule: {name} {running_flag}'.format(
            name=schedule.name, running_flag=running_flag
        )

        if not first:
            print_fn('*' * len(schedule_title))
        first = False

        print_fn(schedule_title)
        print_fn('Cron Schedule: {cron_schedule}'.format(cron_schedule=schedule.cron_schedule))

        if verbose:
            print_fn(
                'Execution Params: {execution_params}'.format(
                    execution_params=schedule.execution_params
                )
            )


def extract_schedule_name(schedule_name):
    if schedule_name and not isinstance(schedule_name, six.string_types):
        if len(schedule_name) == 1:
            return schedule_name[0]
        else:
            check.failed(
                'Can only handle zero or one schedule args. Got {schedule_name}'.format(
                    schedule_name=repr(schedule_name)
                )
            )


@click.command(name='start', help="[Experimental] Start a schedule")
@click.argument('schedule_name', nargs=-1)
@repository_target_argument
def schedule_start_command(schedule_name, **kwargs):
    schedule_name = extract_schedule_name(schedule_name)
    return execute_start_command(schedule_name, kwargs, click.echo)


def execute_start_command(schedule_name, cli_args, print_fn):
    handle = handle_for_repo_cli_args(cli_args)
    repository = handle.build_repository_definition()
    schedule_dir = DagsterInstance.get().schedules_directory()

    python_path = sys.executable
    repository_path = handle.data.repository_yaml

    scheduler = repository.build_scheduler(schedule_dir=schedule_dir)
    if not scheduler:
        print_fn("Scheduler not defined for repository {name}".format(name=repository.name))
        return
    schedule_definition = repository.get_schedule(schedule_name)

    try:
        schedule = scheduler.start_schedule(schedule_definition, python_path, repository_path)
    except DagsterInvariantViolationError as ex:
        raise click.UsageError(ex)

    print_fn(
        "Started schedule {schedule_name} with ID {schedule_id}".format(
            schedule_name=schedule_definition.name, schedule_id=schedule.schedule_id
        )
    )


@click.command(name='end', help="[Experimental] End a schedule")
@click.argument('schedule_name', nargs=-1)
@repository_target_argument
def schedule_end_command(schedule_name, **kwargs):
    schedule_name = extract_schedule_name(schedule_name)
    return execute_end_command(schedule_name, kwargs, click.echo)


def execute_end_command(schedule_name, cli_args, print_fn):
    handle = handle_for_repo_cli_args(cli_args)
    repository = handle.build_repository_definition()
    schedule_dir = DagsterInstance.get().schedules_directory()

    scheduler = repository.build_scheduler(schedule_dir=schedule_dir)
    if not scheduler:
        print_fn("Scheduler not defined for repository {name}".format(name=repository.name))
        return
    schedule_definition = repository.get_schedule(schedule_name)

    try:
        schedule = scheduler.end_schedule(schedule_definition)
    except DagsterInvariantViolationError as ex:
        raise click.UsageError(ex)

    print_fn(
        "Ended schedule {schedule_name} with ID {schedule_id}".format(
            schedule_name=schedule_definition.name, schedule_id=schedule.schedule_id
        )
    )
