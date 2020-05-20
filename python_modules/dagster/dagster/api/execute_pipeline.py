import json
import os
import uuid

from dagster import check
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.instance import DagsterInstance
from dagster.serdes import serialize_dagster_namedtuple
from dagster.serdes.ipc import ipc_read_event_stream
from dagster.seven.temp_dir import get_system_temp_directory
from dagster.utils.temp_file import get_temp_dir


def escape_json_string_for_command(json_string):
    quote_charcter = r'"'
    escaped_quote_charcter = r"\""
    return json_string.replace(quote_charcter, escaped_quote_charcter)


def api_execute_pipeline(instance, recon_repo, pipeline_name, environment_dict, mode, solid_subset):
    check.inst_param(instance, 'instance', DagsterInstance)
    check.inst_param(recon_repo, 'recon_repo', ReconstructableRepository)
    check.str_param(pipeline_name, 'pipeline_name')
    check.dict_param(environment_dict, 'environment_dict')
    check.str_param(mode, 'mode')
    check.opt_list_param(solid_subset, 'solid_subset', of_type=str)

    check.param_invariant(
        recon_repo.yaml_path, 'recon_repo', 'Only support yaml-based repositories for now'
    )

    with get_temp_dir(in_directory=get_system_temp_directory()) as tmp_dir:

        output_file_name = "{}.json".format(uuid.uuid4())
        output_file = os.path.join(tmp_dir, output_file_name)

        environment_dict_string = escape_json_string_for_command(json.dumps(environment_dict))
        instance_ref_string = escape_json_string_for_command(
            serialize_dagster_namedtuple(instance.get_ref())
        )

        command = (
            "dagster api execute_pipeline -y {repository_file} {pipeline_name} "
            '{output_file} --environment-dict="{environment_dict}" --mode={mode} '
            '--instance-ref="{instance_ref}"'
        ).format(
            repository_file=recon_repo.yaml_path,
            pipeline_name=pipeline_name,
            output_file=output_file,
            environment_dict=environment_dict_string,
            mode=mode,
            instance_ref=instance_ref_string,
        )

        if solid_subset:
            command += " --solid_subset={solid_subset}".format(solid_subset=",".join(solid_subset))

        os.popen(command)

        for message in ipc_read_event_stream(output_file):
            yield message
