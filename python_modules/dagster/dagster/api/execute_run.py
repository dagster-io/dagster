import os
import subprocess
import uuid

from dagster import check
from dagster.core.events import EngineEventData
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes import serialize_dagster_namedtuple
from dagster.serdes.ipc import ipc_read_event_stream
from dagster.seven.temp_dir import get_system_temp_directory
from dagster.utils.temp_file import get_temp_dir


# mostly for test
def sync_cli_api_execute_run(
    instance, repo_yaml, pipeline_name, environment_dict, mode, solid_subset
):
    with get_temp_dir(in_directory=get_system_temp_directory()) as tmp_dir:
        output_file_name = "{}.json".format(uuid.uuid4())
        output_file = os.path.join(tmp_dir, output_file_name)
        pipeline_run = instance.create_run(
            pipeline_name=pipeline_name,
            run_id=None,
            environment_dict=environment_dict,
            mode=mode,
            solid_subset=solid_subset,
            step_keys_to_execute=None,
            status=None,
            tags=None,
            root_run_id=None,
            parent_run_id=None,
            pipeline_snapshot=None,
            execution_plan_snapshot=None,
        )
        process = cli_api_execute_run(output_file, instance, repo_yaml, pipeline_run)

        _stdout, _stderr = process.communicate()
        for message in ipc_read_event_stream(output_file):
            yield message


def cli_api_execute_run(output_file, instance, repo_yaml, pipeline_run):
    check.str_param(output_file, 'output_file')
    check.inst_param(instance, 'instance', DagsterInstance)
    check.str_param(repo_yaml, 'repo_yaml')
    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

    parts = [
        'dagster',
        'api',
        'execute_run',
        '-y',
        repo_yaml,
        output_file,
        '--instance-ref={instance_ref}'.format(
            instance_ref=serialize_dagster_namedtuple(instance.get_ref()),
        ),
        '--pipeline-run={pipeline_run}'.format(
            pipeline_run=serialize_dagster_namedtuple(pipeline_run)
        ),
    ]

    instance.report_engine_event(
        'About to start process for pipeline "{pipeline_name}" (run_id: {run_id}).'.format(
            pipeline_name=pipeline_run.pipeline_name, run_id=pipeline_run.run_id
        ),
        pipeline_run,
        engine_event_data=EngineEventData(marker_start='cli_api_subprocess_init'),
    )

    return subprocess.Popen(parts)
