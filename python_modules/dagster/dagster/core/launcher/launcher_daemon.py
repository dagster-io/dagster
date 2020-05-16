import os
import subprocess

from dagster import EventMetadataEntry, check, seven
from dagster.core.events import EngineEventData
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes import ConfigurableClass

from .launcher_base import RunLauncher


class DaemonRunLauncher(RunLauncher, ConfigurableClass):
    '''RunLauncher that starts daemon process for each pipeline run

    Encapsulates each pipeline run in a separate, isolated invocation of ``dagster-graphql``.

    You may configure a Dagster instance to use this RunLauncher by adding a section to your
    ``dagster.yaml`` like the following:

    .. code-block:: yaml

        run_launcher:
            module: dagster.core.launcher
            class: DaemonRunLauncher
    '''
    def __init__(self):
        print('FOOOOOOO INIT')
        super().__init__(self)

    def launch_run(self, instance, run):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(run, 'run', PipelineRun)

        job_name = 'dagster-run-%s' % run.run_id

        print('HIHIHIHIHIHIHIHI')

        subprocess.Popen([
            'dagster-graphql',
            '-p', 'startPipelineExecutionForCreatedRun',
            '-v', seven.json.dumps({'runId': run.run_id}),
        ], env=os.environ)

        instance.report_engine_event(
            'Daemon job launched',
            run,
            EngineEventData(
                [
                    EventMetadataEntry.text(job_name, 'Daemon Job name'),
                    EventMetadataEntry.text(run.run_id, 'Run ID'),
                ]
            ),
            cls=DaemonRunLauncher,
        )
        return run
