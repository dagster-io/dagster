import os
import warnings
from uuid import uuid4

from dagster import DagsterInvariantViolationError, check
from dagster.core.snap import ActiveRepositoryData
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.seven import get_system_temp_directory
from dagster.utils.temp_file import get_temp_dir

DEFAULT_INTERNAL_VOLUME = '/data'
DEFAULT_MODE = 'rw'


def run_serialized_container_command(image, command, volumes):
    try:
        from docker.client import from_env

        client = from_env()
        client.containers.run(
            image, command=command, detach=False, volumes=volumes, auto_remove=True,
        )
    except ImportError:
        warnings.warn(
            "Cannot load docker environment without the python package docker. Ensure that dagster[docker] or the python package docker is installed."
        )
        raise


def _get_active_repo_data(path):
    with open(path, 'r') as fp:
        return deserialize_json_to_dagster_namedtuple(fp.read())


def get_active_repository_data_from_image(image):
    check.str_param(image, 'image')

    with get_temp_dir(in_directory=get_system_temp_directory()) as tmp_dir:
        output_file_name = "{}.json".format(uuid4())
        run_serialized_container_command(
            image=image,
            command='dagster repository snapshot {output_file}'.format(
                output_file=os.path.join(DEFAULT_INTERNAL_VOLUME, output_file_name)
            ),
            volumes={tmp_dir: {'bind': DEFAULT_INTERNAL_VOLUME, 'mode': DEFAULT_MODE}},
        )

        active_repo_data = _get_active_repo_data(os.path.join(tmp_dir, output_file_name))
        if not isinstance(active_repo_data, ActiveRepositoryData):
            raise DagsterInvariantViolationError(
                "Deserialized snapshot is of type {received} must be a ActiveRepositoryData".format(
                    received=type(active_repo_data)
                )
            )
        return active_repo_data
