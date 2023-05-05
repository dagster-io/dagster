import os
import tempfile
from contextlib import contextmanager
from typing import Callable, Iterator, Optional

import click

from dagster._core.instance import DagsterInstance, InstanceRef
from dagster._core.instance.config import is_dagster_home_set


@contextmanager
def get_instance_for_service(
    service_name: str,
    instance_ref: Optional[InstanceRef] = None,
    logger_fn: Callable[[str], None] = click.echo,
) -> Iterator[DagsterInstance]:
    if instance_ref:
        with DagsterInstance.from_ref(instance_ref) as instance:
            yield instance
    elif is_dagster_home_set():
        with DagsterInstance.get() as instance:
            yield instance
    else:
        # make the temp dir in the cwd since default temp dir roots
        # have issues with FS notify-based event log watching
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tempdir:
            logger_fn(
                f"Using temporary directory {tempdir} for storage. This will be removed when"
                f" {service_name} exits."
            )
            logger_fn(
                "To persist information across sessions, set the environment variable DAGSTER_HOME"
                " to a directory to use."
            )

            with DagsterInstance.from_ref(
                InstanceRef.from_dir(tempdir, config_dir=os.getcwd())
            ) as instance:
                yield instance
