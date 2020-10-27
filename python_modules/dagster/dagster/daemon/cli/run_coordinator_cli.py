import click
from dagster import DagsterInstance
from dagster.daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon


def create_run_coordinator_cli_group():
    group = click.Group()
    group.add_command(run_command)
    return group


@click.command(
    name="run", help="Poll for queued runs and launch them",
)
@click.option(
    "--interval-seconds", help="How long to wait (seconds) between polls for runs", default=2
)
@click.option(
    "--max-concurrent-runs", help="Max number of runs that should be executing at once", default=10,
)
def run_command(interval_seconds, max_concurrent_runs):
    coordinator = QueuedRunCoordinatorDaemon(
        DagsterInstance.get(), max_concurrent_runs=max_concurrent_runs
    )
    click.echo("Starting run coordinator")
    coordinator.run(interval_seconds=interval_seconds)
