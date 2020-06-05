import sys

from dagster import DagsterInvariantViolationError, check
from dagster.core.events import EngineEventData
from dagster.core.host_representation.handle import (
    InProcessRepositoryLocationHandle,
    PythonEnvRepositoryLocationHandle,
    RepositoryHandle,
)
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes import serialize_dagster_namedtuple
from dagster.serdes.ipc import ipc_read_event_stream, open_ipc_subprocess
from dagster.seven import xplat_shlex_split
from dagster.utils import safe_tempfile_path


# mostly for test
def sync_cli_api_execute_run(
    instance, repo_handle, pipeline_name, environment_dict, mode, solids_to_execute
):
    with safe_tempfile_path() as output_file_path:
        pipeline_run = instance.create_run(
            pipeline_name=pipeline_name,
            run_id=None,
            environment_dict=environment_dict,
            mode=mode,
            solids_to_execute=solids_to_execute,
            step_keys_to_execute=None,
            status=None,
            tags=None,
            root_run_id=None,
            parent_run_id=None,
            pipeline_snapshot=None,
            execution_plan_snapshot=None,
            parent_pipeline_snapshot=None,
        )
        process = cli_api_execute_run(output_file_path, instance, repo_handle, pipeline_run)

        _stdout, _stderr = process.communicate()
        for message in ipc_read_event_stream(output_file_path):
            yield message


def cli_api_execute_run(output_file, instance, repository_handle, pipeline_run):
    check.str_param(output_file, 'output_file')
    check.inst_param(instance, 'instance', DagsterInstance)
    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

    pointer = repository_handle.get_pointer()
    location_handle = repository_handle.repository_location_handle

    if isinstance(location_handle, PythonEnvRepositoryLocationHandle):
        executable_path = location_handle.executable_path
    elif isinstance(location_handle, InProcessRepositoryLocationHandle):
        # [legacy] default to using sys.executable for the in process
        # location handle
        executable_path = sys.executable
    else:
        raise DagsterInvariantViolationError(
            "Unable to resolve executable_path for repository location handle of type {}".format(
                location_handle.__class__
            )
        )

    executable_path = (
        location_handle.executable_path
        if isinstance(location_handle, PythonEnvRepositoryLocationHandle)
        else sys.executable
    )

    parts = (
        [executable_path, '-m', 'dagster', 'api', 'execute_run', output_file]
        + xplat_shlex_split(pointer.get_cli_args())
        + [
            '--instance-ref',
            '{instance_ref}'.format(instance_ref=serialize_dagster_namedtuple(instance.get_ref())),
            '--pipeline-run',
            '{pipeline_run}'.format(pipeline_run=serialize_dagster_namedtuple(pipeline_run)),
        ]
    )

    instance.report_engine_event(
        'About to start process for pipeline "{pipeline_name}" (run_id: {run_id}).'.format(
            pipeline_name=pipeline_run.pipeline_name, run_id=pipeline_run.run_id
        ),
        pipeline_run,
        engine_event_data=EngineEventData(marker_start='cli_api_subprocess_init'),
    )

    return open_ipc_subprocess(parts)
