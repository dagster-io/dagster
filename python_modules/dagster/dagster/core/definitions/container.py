import os
import warnings
from uuid import uuid4

from dagster import DagsterInvariantViolationError, check
from dagster.core.snap.repository_snapshot import RepositorySnapshot
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.seven import get_system_temp_directory
from dagster.utils.temp_file import get_temp_dir

DEFAULT_INTERNAL_VOLUME = '/data'
DEFAULT_MODE = 'rw'


def run_serialized_container_command(image, command, volumes):
    try:
        from docker.client import from_env
    except ImportError:
        warnings.warn(
            "Cannot load docker environment without the python package docker. Ensure that dagster[docker] or the python package docker is installed."
        )
        raise

    client = from_env()
    client.containers.run(image, command=command, detach=False, volumes=volumes, auto_remove=True)


def get_container_snapshot(image):
    check.str_param(image, 'image')
    # Done to avoid memory leaks
    with get_temp_dir(in_directory=get_system_temp_directory()) as tmp_dir:
        # TODO: Add better error handling when we move towards integrating with dagit.
        output_file_name = "{}.json".format(uuid4())
        run_serialized_container_command(
            image=image,
            command='dagster repository snapshot {output_file}'.format(
                output_file=os.path.join(DEFAULT_INTERNAL_VOLUME, output_file_name)
            ),
            volumes={tmp_dir: {'bind': DEFAULT_INTERNAL_VOLUME, 'mode': DEFAULT_MODE,}},
        )

        with open(os.path.join(tmp_dir, output_file_name), 'r') as fp:
            snapshot = deserialize_json_to_dagster_namedtuple(fp.read())
        if not isinstance(snapshot, RepositorySnapshot):
            raise DagsterInvariantViolationError(
                "Deserialized snapshot is of type {received} must be a RepositorySnapshot".format(
                    received=type(snapshot)
                )
            )
    return snapshot
