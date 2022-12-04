import os
import tempfile
from contextlib import contextmanager

import click

from dagster._core.instance import DagsterInstance
from dagster._core.instance.config import is_dagster_home_set


@contextmanager
def get_instance_for_service(service_name):
    if is_dagster_home_set():
        with DagsterInstance.get() as instance:
            yield instance
    else:
        # make the temp dir in the cwd since default temp dir roots
        # have issues with FS notif based event log watching
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tempdir:
            click.echo(
                f"Using temporary directory {tempdir} for storage. This will be removed when"
                f" {service_name} exits.\nTo persist information across sessions, set the"
                " environment variable DAGSTER_HOME to a directory to use.\n"
            )
            with DagsterInstance.local_temp(tempdir) as instance:
                yield instance
