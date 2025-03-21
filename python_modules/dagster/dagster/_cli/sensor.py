import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional

import click
from dagster_shared.yaml_utils import dump_run_config_yaml

from dagster import (
    DagsterInvariantViolationError,
    __version__ as dagster_version,
)
from dagster._cli.utils import (
    assert_no_remaining_opts,
    get_instance_for_cli,
    validate_dagster_home_is_set,
    validate_repo_has_defined_sensors,
)
from dagster._cli.workspace.cli_target import (
    RepositoryOpts,
    WorkspaceOpts,
    get_code_location_from_workspace,
    get_remote_repository_from_code_location,
    get_repository_from_cli_opts,
    get_workspace_from_cli_opts,
    repository_options,
    workspace_options,
)
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation import RemoteRepository
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    SensorInstigatorData,
)
from dagster._utils import PrintFn
from dagster._utils.error import serializable_error_info_from_exc_info


@click.group(name="sensor")
def sensor_cli():
    """Commands for working with Dagster sensors."""


@sensor_cli.command(
    name="list",
    help="List all sensors that correspond to a repository.",
)
@click.option(
    "--running", "running_filter", help="Filter for running sensors", is_flag=True, default=False
)
@click.option(
    "--stopped", "stopped_filter", help="Filter for stopped sensors", is_flag=True, default=False
)
@click.option(
    "--name", "name_filter", help="Only display sensor sensor names", is_flag=True, default=False
)
@workspace_options
@repository_options
def sensor_list_command(
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

        repo_sensors = repo.get_sensors()
        stored_sensors_by_origin_id = {
            stored_sensor_state.instigator_origin_id: stored_sensor_state
            for stored_sensor_state in instance.all_instigator_state(
                repo.get_remote_origin_id(),
                repo.selector_id,
                instigator_type=InstigatorType.SENSOR,
            )
        }

        first = True

        for sensor in repo_sensors:
            sensor_state = sensor.get_current_instigator_state(
                stored_sensors_by_origin_id.get(sensor.get_remote_origin_id())
            )

            if running_filter and not sensor_state.is_running:
                continue
            if stopped_filter and sensor_state.is_running:
                continue

            if name_filter:
                print_fn(sensor.name)
                continue

            status = "RUNNING" if sensor_state.is_running else "STOPPED"
            sensor_title = f"Sensor: {sensor.name} [{status}]"
            if not first:
                print_fn("*" * len(sensor_title))

            first = False

            print_fn(sensor_title)


@sensor_cli.command(name="start", help="Start an existing sensor.")
@click.argument("sensor_name", required=False)
@click.option("--start-all", help="start all sensors", is_flag=True, default=False)
@workspace_options
@repository_options
def sensor_start_command(sensor_name: Optional[str], start_all: bool, **other_opts: object):
    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    repository_opts = RepositoryOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)
    return execute_start_command(
        sensor_name=sensor_name,
        start_all=start_all,
        workspace_opts=workspace_opts,
        repository_opts=repository_opts,
        print_fn=click.echo,
    )


def execute_start_command(
    *,
    sensor_name: Optional[str],
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
            try:
                for sensor in repo.get_sensors():
                    instance.start_sensor(sensor)
                print_fn(f"Started all sensors for repository {repo.name}")
            except DagsterInvariantViolationError as ex:
                raise click.UsageError(ex)  # pyright: ignore[reportArgumentType]
        else:
            if not sensor_name:
                raise click.UsageError("Missing sensor name argument")
            try:
                sensor = repo.get_sensor(sensor_name)
                instance.start_sensor(sensor)
            except DagsterInvariantViolationError as ex:
                raise click.UsageError(ex)  # pyright: ignore[reportArgumentType]

            print_fn(f"Started sensor {sensor_name}")


@sensor_cli.command(name="stop", help="Stop an existing sensor.")
@click.argument("sensor_name")
@workspace_options
@repository_options
def sensor_stop_command(sensor_name: str, **other_opts: object):
    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    repository_opts = RepositoryOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)
    return execute_stop_command(
        sensor_name=sensor_name,
        workspace_opts=workspace_opts,
        repository_opts=repository_opts,
        print_fn=click.echo,
    )


def execute_stop_command(
    *,
    sensor_name: str,
    workspace_opts: WorkspaceOpts,
    repository_opts: RepositoryOpts,
    print_fn: PrintFn,
):
    with (
        get_instance_for_cli() as instance,
        _get_repo(workspace_opts, repository_opts, instance) as repo,
    ):
        try:
            sensor = repo.get_sensor(sensor_name)
            instance.stop_sensor(
                sensor.get_remote_origin_id(),
                sensor.selector_id,
                sensor,
            )
        except DagsterInvariantViolationError as ex:
            raise click.UsageError(ex)  # pyright: ignore[reportArgumentType]

        print_fn(f"Stopped sensor {sensor_name}")


@sensor_cli.command(name="preview", help="Preview an existing sensor execution.")
@click.argument("sensor_name")
@click.option(
    "--since",
    type=float,
    help="Set the last_tick_completion_time value as a timestamp float for the sensor context",
    default=None,
)
@click.option(
    "--last_run_key",
    help="Set the last_run_key value for the sensor context",
    default=None,
)
@click.option(
    "--cursor",
    help="Set the cursor value for the sensor context",
    default=None,
)
@workspace_options
@repository_options
def sensor_preview_command(
    sensor_name: str,
    since: Optional[float],
    last_run_key: Optional[str],
    cursor: Optional[str],
    **other_opts: object,
):
    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    repository_opts = RepositoryOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)

    return execute_preview_command(
        sensor_name=sensor_name,
        since=since,
        last_run_key=last_run_key,
        cursor=cursor,
        workspace_opts=workspace_opts,
        repository_opts=repository_opts,
        print_fn=click.echo,
    )


def execute_preview_command(
    *,
    sensor_name: str,
    since: Optional[float],
    last_run_key: Optional[str],
    cursor: Optional[str],
    workspace_opts: WorkspaceOpts,
    repository_opts: RepositoryOpts,
    print_fn: PrintFn,
    instance: Optional[DagsterInstance] = None,
):
    # We don't call _get_repo here because we need the code location.
    with (
        get_instance_for_cli() as instance,
        get_workspace_from_cli_opts(
            instance, version=dagster_version, workspace_opts=workspace_opts
        ) as workspace,
    ):
        code_location = get_code_location_from_workspace(workspace, repository_opts.location)
        repo = get_remote_repository_from_code_location(code_location, repository_opts.repository)
        validate_repo_has_defined_sensors(repo)
        validate_dagster_home_is_set()
        try:
            sensor = repo.get_sensor(sensor_name)
            sensor_runtime_data = code_location.get_sensor_execution_data(
                instance,
                repo.handle,
                sensor.name,
                since,
                last_run_key,
                cursor,
                log_key=None,
                last_sensor_start_time=None,
            )
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            print_fn(f"Failed to resolve sensor for {sensor.name} : {error_info.to_string()}")  # pyright: ignore[reportPossiblyUnboundVariable]
            return

        if not sensor_runtime_data.run_requests:
            if sensor_runtime_data.skip_message:
                print_fn(
                    f"Sensor returned false for {sensor.name}, skipping: {sensor_runtime_data.skip_message}"
                )
            else:
                print_fn(f"Sensor returned false for {sensor.name}, skipping")
        else:
            print_fn(
                "Sensor returning run requests for {num} run(s):\n\n{run_requests}".format(
                    num=len(sensor_runtime_data.run_requests),
                    run_requests="\n".join(
                        dump_run_config_yaml(run_request.run_config)
                        for run_request in sensor_runtime_data.run_requests
                    ),
                )
            )


@sensor_cli.command(name="cursor", help="Set the cursor value for an existing sensor.")
@click.argument("sensor_name")
@click.option(
    "--set",
    "cursor_value",
    help="Set the cursor value for the sensor context",
    default=None,
)
@click.option(
    "--delete", help="Delete the existing cursor value for the sensor context", is_flag=True
)
@workspace_options
@repository_options
def sensor_cursor_command(
    sensor_name: str, cursor_value: Optional[str], delete: bool, **other_opts: object
):
    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    repository_opts = RepositoryOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)
    return execute_cursor_command(
        sensor_name=sensor_name,
        cursor_value=cursor_value,
        delete=delete,
        workspace_opts=workspace_opts,
        repository_opts=repository_opts,
        print_fn=click.echo,
    )


def execute_cursor_command(
    *,
    sensor_name: str,
    cursor_value: Optional[str],
    delete: bool,
    workspace_opts: WorkspaceOpts,
    repository_opts: RepositoryOpts,
    print_fn: PrintFn,
):
    if bool(delete) == bool(cursor_value):
        # must use one of delete/set
        raise click.UsageError("Must set cursor using `--set <value>` or use `--delete`")

    with (
        get_instance_for_cli() as instance,
        _get_repo(workspace_opts, repository_opts, instance) as repo,
    ):
        sensor = repo.get_sensor(sensor_name)
        job_state = instance.get_instigator_state(sensor.get_remote_origin_id(), sensor.selector_id)
        if not job_state:
            instance.add_instigator_state(
                InstigatorState(
                    sensor.get_remote_origin(),
                    InstigatorType.SENSOR,
                    InstigatorStatus.STOPPED,
                    SensorInstigatorData(
                        min_interval=sensor.min_interval_seconds,
                        cursor=cursor_value,
                        sensor_type=sensor.sensor_type,
                    ),
                )
            )
        else:
            instance.update_instigator_state(
                job_state.with_data(
                    SensorInstigatorData(
                        last_tick_timestamp=job_state.instigator_data.last_tick_timestamp,  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
                        last_run_key=job_state.instigator_data.last_run_key,  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
                        min_interval=sensor.min_interval_seconds,
                        cursor=cursor_value,
                        last_tick_start_timestamp=job_state.instigator_data.last_tick_start_timestamp,  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
                        last_sensor_start_timestamp=job_state.instigator_data.last_sensor_start_timestamp,  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
                        sensor_type=sensor.sensor_type,
                    ),
                )
            )
        if cursor_value:
            print_fn(f'Set cursor state for sensor {sensor.name} to "{cursor_value}"')
        else:
            print_fn(f"Cleared cursor state for sensor {sensor.name}")


# ########################
# ##### HELPERS
# ########################


def print_changes(
    remote_repository: RemoteRepository,
    instance: DagsterInstance,
    print_fn: PrintFn = print,
    preview: bool = False,
) -> None:
    sensor_states = instance.all_instigator_state(
        remote_repository.get_remote_origin_id(),
        remote_repository.selector_id,
        InstigatorType.SENSOR,
    )
    sensors = remote_repository.get_sensors()
    sensors_dict = {s.get_remote_origin_id(): s for s in sensors}
    sensor_states_dict = {s.instigator_origin_id: s for s in sensor_states}

    sensor_origin_ids = set(sensors_dict.keys())
    sensor_state_ids = set(sensor_states_dict.keys())

    added_sensors = sensor_origin_ids - sensor_state_ids
    removed_sensors = sensor_state_ids - sensor_origin_ids

    if not added_sensors and not removed_sensors:
        if preview:
            print_fn(click.style("No planned changes to sensors.", fg="magenta", bold=True))
            print_fn(f"{len(sensors)} sensors will remain unchanged")
        else:
            print_fn(click.style("No changes to sensors.", fg="magenta", bold=True))
            print_fn(f"{len(sensors)} sensors unchanged")
        return

    print_fn(
        click.style("Planned Sensor Changes:" if preview else "Changes:", fg="magenta", bold=True)
    )

    for sensor_origin_id in added_sensors:
        print_fn(
            click.style(
                f"  + {sensors_dict[sensor_origin_id].name} (add) [{sensor_origin_id}]",
                fg="green",
            )
        )

    for sensor_origin_id in removed_sensors:
        print_fn(
            click.style(
                f"  + {sensors_dict[sensor_origin_id].name} (delete) [{sensor_origin_id}]",
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
        validate_repo_has_defined_sensors(repo)
        validate_dagster_home_is_set()
        yield repo


def check_repo_and_scheduler(repository: RemoteRepository, instance: DagsterInstance) -> None:
    repository_name = repository.name

    if not repository.get_sensors():
        raise click.UsageError(f"There are no sensors defined for repository {repository_name}.")

    if not os.getenv("DAGSTER_HOME"):
        raise click.UsageError(
            "The environment variable $DAGSTER_HOME is not set. Dagster requires this "
            "environment variable to be set to an existing directory in your filesystem "
            "that contains your dagster instance configuration file (dagster.yaml).\n"
            "You can resolve this error by exporting the environment variable."
            "For example, you can run the following command in your shell or "
            "include it in your shell configuration file:\n"
            '\texport DAGSTER_HOME="~/dagster_home"'
            "\n\n"
        )
