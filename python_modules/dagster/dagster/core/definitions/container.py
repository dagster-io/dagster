import json
import os
import warnings
from uuid import uuid4

from dagster import DagsterInvariantViolationError, check
from dagster.core.definitions.mode import DEFAULT_MODE_NAME
from dagster.core.host_representation import ExternalRepository, ExternalRepositoryData
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.serdes.ipc import ipc_read_event_stream
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


def _deserialize_line(line):
    return deserialize_json_to_dagster_namedtuple(line.rstrip())


def run_detached_container_command(image, command, volumes, output_file):

    try:
        from docker.client import from_env

        client = from_env()

        # This is currently blocking. Has to be updated to run in detached mode. The problem
        # is knowing when the file is ready to be read from.
        client.containers.run(image, command=command, volumes=volumes, auto_remove=False)

        for message in ipc_read_event_stream(output_file):
            yield message

    except ImportError:
        warnings.warn(
            "Cannot load docker environment without the python package docker. Ensure that dagster[docker] or the python package docker is installed."
        )
        raise


def get_external_repository_from_image(image):
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

        serialized_external_repo_data = output[0]
        external_repo_data = deserialize_json_to_dagster_namedtuple(serialized_external_repo_data)

        if not isinstance(external_repo_data, ExternalRepositoryData):
            raise DagsterInvariantViolationError(
                "Deserialized snapshot is of type {received} must be a ExternalRepositoryData".format(
                    received=type(external_repo_data)
                )
            )
        return ExternalRepository(external_repo_data)


def execute_pipeline_iterator_from_image(
    image, pipeline_name, environment_dict=None, mode=None, solid_subset=None
):
    # This method currently depends on file mounts, and will not work when executing within
    # a docker container

    check.str_param(image, 'image')
    check.str_param(pipeline_name, 'pipeline_name')
    check.opt_dict_param(environment_dict, 'environment-dict', key_type=str)
    mode = check.opt_str_param(mode, 'mode', DEFAULT_MODE_NAME)
    check.opt_list_param(solid_subset, 'solid-subset', of_type="str")

    if not environment_dict:
        environment_dict = {}

    with get_temp_dir(in_directory=get_system_temp_directory()) as tmp_dir:
        output_file_name = "{}.json".format(uuid4())

        command = (
            "dagster api execute_pipeline -y repository.yaml {pipeline_name} "
            "{output_file} --environment-dict='{environment_dict}' --mode={mode}".format(
                pipeline_name=pipeline_name,
                output_file=os.path.join(DEFAULT_INTERNAL_VOLUME, output_file_name),
                environment_dict=json.dumps(environment_dict),
                mode=mode,
            )
        )

        if solid_subset:
            command += " --solid_subset={solid_subset}".format(solid_subset=",".join(solid_subset))

        for event in run_detached_container_command(
            image=image,
            command=command,
            volumes={tmp_dir: {'bind': DEFAULT_INTERNAL_VOLUME, 'mode': DEFAULT_MODE}},
            output_file=os.path.join(tmp_dir, output_file_name),
        ):
            yield event
