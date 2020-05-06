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
        byte_stream = client.containers.run(
            image, command=command, volumes=volumes, auto_remove=False,
        )

        # Decode to string, split by newlines, and filter for any empty strings
        lines = list(filter(None, byte_stream.decode('utf-8').split("\n")))
        return lines
    except ImportError:
        warnings.warn(
            "Cannot load docker environment without the python package docker. Ensure that dagster[docker] or the python package docker is installed."
        )
        raise


def get_active_repository_data_from_image(image):
    check.str_param(image, 'image')

    with get_temp_dir(in_directory=get_system_temp_directory()) as tmp_dir:
        output_file_name = "{}.json".format(uuid4())
        command = 'dagster api snapshot repository'.format(
            output_file=os.path.join(DEFAULT_INTERNAL_VOLUME, output_file_name)
        )
        output = run_serialized_container_command(
            image=image,
            command=command,
            volumes={tmp_dir: {'bind': DEFAULT_INTERNAL_VOLUME, 'mode': DEFAULT_MODE}},
        )

        if len(output) != 1:
            print(output)
            raise DagsterInvariantViolationError(
                "Running command {command} in container {image} resulted in output of length "
                "{actual} lines, expected {expected} lines".format(
                    command=command, image=image, actual=len(output), expected=1
                )
            )

        serialized_active_repo_data = output[0]
        active_repo_data = deserialize_json_to_dagster_namedtuple(serialized_active_repo_data)

        if not isinstance(active_repo_data, ActiveRepositoryData):
            raise DagsterInvariantViolationError(
                "Deserialized snapshot is of type {received} must be a ActiveRepositoryData".format(
                    received=type(active_repo_data)
                )
            )
        return active_repo_data
