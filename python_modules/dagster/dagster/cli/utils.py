import tempfile
from contextlib import contextmanager

import click
from dagster import seven
from dagster.core.instance import DagsterInstance, is_dagster_home_set


@contextmanager
def get_instance_for_service(service_name):
    if is_dagster_home_set():
        with DagsterInstance.get() as instance:
            yield instance
    else:
        # make the temp dir in system temp since default temp dir roots
        # have issues with FS notif based event log watching
        with tempfile.TemporaryDirectory(dir=seven.get_system_temp_directory()) as tempdir:
            click.echo(
                f"Using temporary directory {tempdir} for storage. This will be removed when {service_name} exits.\n"
                "To persist information across sessions, set the environment variable DAGSTER_HOME to a directory to use.\n"
            )
            with DagsterInstance.local_temp(tempdir) as instance:
                yield instance
